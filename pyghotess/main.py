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
from fastapi import Depends, FastAPI, HTTPException, File, UploadFile
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
VERSION = 1
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
