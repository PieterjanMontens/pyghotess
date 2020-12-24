#!/usr/bin/env python3
#  Pyghotess, fast image-PDF OCR Processing
#     Copyright (C) 2020    Pieterjan Montens
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import logging
import shutil
import os
import argparse
import uvicorn
import toml
import tempfile
import json
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    File,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from typing import List
from fastapi.responses import PlainTextResponse
from starlette.middleware.cors import CORSMiddleware
import pyghotess.lib_misc as lm
import pyghotess.lib_parse as lp


# ################################################### SETUP AND ARGUMENT PARSING
# ##############################################################################
logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())
dir_path = os.path.dirname(os.path.realpath(__file__))

config = {
    'server': {
        'host': os.getenv('HOST', '127.0.0.1'),
        'port': int(os.getenv('PORT', '5000')),
        'log_level': os.getenv('LOG_LEVEL', 'info'),
        'timeout_keep_alive': 0,
    },
    'proxy_prefix': os.getenv('PROXY_PREFIX', ''),
    'log_level': 'info',
    'access_key': os.getenv('ACCESS_KEY', False),
    'extract': {
        'resolution': os.getenv('RESOLUTION', 200),
        'alphaBits': 4,
    },
    'ocr': {
        'resolution': os.getenv('RESOLUTION', 200),
        'workers': os.getenv('WORKERS', 2),
        'psm': 4
    }
}


COUNTER = 0
VERSION = 3
START_TIME = lm.starttime_get()

# ################################################################## APP CONFIG
# #############################################################################


app = FastAPI(root_path=config['proxy_prefix'])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# ############################################################### SERVER ROUTES
# #############################################################################
@app.get("/")
def root():
    return lm.status_get(START_TIME, VERSION, COUNTER)


@app.post("/process")
async def process(rawFile: UploadFile = File(...)):
    """
    Process
    Execute OCR Processing on uploaded file
    """
    with tempfile.NamedTemporaryFile() as tFile:
        shutil.copyfileobj(rawFile.file, tFile.file)

        with lp.pdf2png(config, tFile.name) as (taskid, path):
            payload = []
            for fname in os.listdir(path):
                order = int(fname[3:5])
                fpath = os.path.join(path, fname)
                payload.append((order, fpath))

            result = await lp.process(payload, config)
            text = lp.outputParse(result)

    return PlainTextResponse(text)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    status = {}
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            if data['action'] == 'test':
                await ws.send_json(data)
            if data['action'] == 'get_file_status':
                await ws.send_json({
                    'action': 'get_file_status',
                    'payload': status['file']['status']
                })
            if data['action'] == 'upload':
                with tempfile.NamedTemporaryFile() as tFile:
                    status['file'] = {
                        'status': 'uploading',
                        'file': tFile
                    }
                    logger.debug('ready to receive bytes')
                    await ws.send_json({'action': 'upload'})
                    while True:
                        rawBytes = await ws.receive_bytes()
                        tFile.write(rawBytes)
                        if len(rawBytes) == 0:
                            logger.info("File received")
                            break
                        logger.debug("Wrote %s bytes", len(rawBytes))
                    tFile.seek(0)
                    status['file']['status'] = 'uploaded'

                    async def fun(order, text):
                        logger.debug(f'sending text {order} to ws')
                        await ws.send_json({
                            'action': 'page_extract',
                            'meta': {'page': order},
                            'payload': text,
                        })

                    with lp.pdf2png(config, tFile.name) as (taskid, path):
                        payload = []
                        for fname in os.listdir(path):
                            order = int(fname[3:5])
                            fpath = os.path.join(path, fname)
                            payload.append((order, fpath))
                        payload.sort(key=lambda x: x[0])

                        status['file']['status'] = 'OCR processing'
                        await lp.processWithGatherer(payload, config, fun)

                await ws.send_json({'action': 'done'})

    except WebSocketDisconnect:
        manager.disconnect(ws)
        logger.debug("Disconnecting")


# ##################################################################### STARTUP
# #############################################################################
def main():
    global config

    parser = argparse.ArgumentParser(description='Pyghotess API server process')
    parser.add_argument('--config', dest='config', help='config file', default=None)
    parser.add_argument('--debug', dest='debug', action='store_true', default=False, help='Debug mode')
    args = parser.parse_args()

    if args.config:
        t_config = toml.load(['config_default.toml', args.config])
    else:
        t_config = toml.load('config_default.toml')

    config = {**config, **t_config}

    if args.debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.debug('Debug activated')
        config['log_level'] = 'debug'
        config['server']['log_level'] = 'debug'
        logger.debug('Arguments: %s', args)
        logger.debug('config: %s', toml.dumps(config))

    uvicorn.run(
        app,
        **config['server']
    )


if __name__ == "__main__":
    main()
