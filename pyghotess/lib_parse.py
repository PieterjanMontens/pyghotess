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
import os
import uuid
import asyncio
import logging
import shutil
import math
import subprocess
import multiprocessing
from contextlib import contextmanager

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())


def outputParse(listIn):
    listIn.sort(key=lambda x: x[0])
    listOut = [x for _y, x in listIn]
    return '\n'.join(listOut)


@contextmanager
def pdf2png(config, filePath, outDir=False, *, cleanUp=True):
    """
    pdf2png
    - Make a temporary directory
    - Extract PDF pages to PNG with GhostScript
    - Yield directory path
    - Finally and in all cases : clean up temp directory
    """
    taskid = str(uuid.uuid4())

    if not outDir:
        outDir = os.getcwd()

    tempPath = os.path.join(outDir, taskid)
    os.mkdir(tempPath)

    cfg = config.get('extract', {'resolution': 200, 'alphaBits': 4})
    logger.info('pdf2png: %s', cfg)
    cmd = [
        'gs',
        '-q',
        '-sDEVICE=png16m',
        f'-dTextAlphaBits={cfg["alphaBits"]}',
        f'-o{tempPath}/gs-%02d.png',
        '-dNOPAUSE',
        f'-r{cfg["resolution"]}',
        filePath,
    ]
    subprocess.run(cmd)

    try:
        yield (taskid, tempPath)

    finally:
        if cleanUp:
            shutil.rmtree(tempPath)


async def worker(name, cfg, language, queue_in, queue_out):
    while True:
        try:
            order, fpath = await queue_in.get()
            logger.info('Worker %s starting on file %s', name, order)
            logger.debug(cfg)

            cmd = [
                'tesseract',
                '--psm', str(cfg['psm']),
                '-l', language,
                '--dpi', str(cfg['resolution']),
                '--oem', '1',
                fpath,
                'stdout',
            ]
            await asyncio.sleep(.1)

            proc = await asyncio.create_subprocess_shell(
                ' '.join(cmd),
                stdout=asyncio.subprocess.PIPE)
            # result = subprocess.run(cmd, stdout=subprocess.PIPE)
            stdout, _ = await proc.communicate()
            queue_out.put_nowait((order, stdout.decode()))
            queue_in.task_done()
        except Exception as e:
            logger.exception(e)


async def process(payloads, config={}, language='fra'):
    queue_in = asyncio.Queue()
    queue_out = asyncio.Queue()

    logger.debug('Filling queue in')
    cfg = config.get('ocr', {'psm': 4, 'dpi': 200, 'workers': 2})

    logger.info('process: %s', cfg)
    for payload in payloads:
        queue_in.put_nowait(payload)

    logger.debug('Creating tasks')
    tasks = []
    if cfg['workers'] == 'auto':
        workers = int(math.ceil(multiprocessing.cpu_count() / 4))
    else:
        workers = int(cfg['workers'])

    for i in range(workers):
        task = asyncio.create_task(worker(
            f'w-{i}',
            cfg,
            language,
            queue_in,
            queue_out
        ))
        tasks.append(task)

    logger.debug('Waiting job execution')
    await queue_in.join()

    logger.debug('Ending workers')
    for task in tasks:
        task.cancel

    resp = []
    logger.debug('Getting results')
    try:
        while True:
            resp.append(queue_out.get_nowait())
    except asyncio.queues.QueueEmpty:
        pass

    # Cancel our worker tasks.
    logger.debug('Cleaning up')
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    return resp


async def processWithGatherer(payloads, config, gatherer, language='fra'):
    queue_in = asyncio.Queue()
    queue_out = asyncio.Queue()

    async def gth(queue_gath):
        while True:
            try:
                order, test = await queue_gath.get()
                logger.debug('Gatherer received %s', order)
                await gatherer(order, test)
                queue_gath.task_done()
            except Exception as e:
                logger.exception(e)

    logger.debug('Filling queue in')
    cfg = config.get('ocr', {'psm': 4, 'dpi': 200, 'workers': 2})

    logger.info('process: %s', cfg)
    for payload in payloads:
        queue_in.put_nowait(payload)

    logger.debug('Creating tasks')
    tasks = []
    if cfg['workers'] == 'auto':
        workers = int(math.ceil(multiprocessing.cpu_count() / 4))
    else:
        workers = int(cfg['workers'])

    for i in range(workers):
        task = asyncio.create_task(worker(
            f'w-{i}',
            cfg,
            language,
            queue_in,
            queue_out
        ))
        tasks.append(task)

    gath_job = asyncio.create_task(gth(queue_out))
    tasks.append(gath_job)

    logger.debug('Waiting job execution')
    await queue_in.join()
    logger.debug('Job done, ending workers')

    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)
