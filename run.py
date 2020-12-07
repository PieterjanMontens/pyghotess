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

import click
import sys
import logging
import os
import time
import math
import asyncio
import pyghotess as pgt

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

config = {
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


@click.group()
@click.option('--debug', '-d', 'debug', default=False,
              help="Activate debugging flag")
def run(debug):
    if debug:
        logger.setLevel(logging.getLevelName('DEBUG'))
        logger.info('Debugging Enabled')


@run.command()
@click.option('--file', '-f', 'fileIn', default="",
              help="Input image-PDF file")
@click.option('--out-dir', '-o', 'outDir', default="",
              help="Root directory for temp directory")
def extract(fileIn, outDir):
    """
    EXTRACT
    Extract PDF files to PNG images
    """
    dirPath = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(dirPath, fileIn)
    if outDir == "":
        outDir = os.getcwd()

    with pgt.pdf2png(config, filePath, outDir, cleanUp=False) as (taskid, path):
        logger.info('Extracted PDF file to directory:/n %s', path)
        sys.stdout.write(path)


@run.command()
@click.option('--dir', '-d', 'directory', default="",
              help="Directory with image files")
def ocr(directory):
    """
    OCR
    Parse directory with PNG images by OCR processing
    and output resulting text.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    work_path = os.path.join(dir_path, directory)

    payload = []
    for fname in os.listdir(directory):
        order = int(fname[3:5])
        fpath = os.path.join(work_path, fname)
        payload.append((order, fpath))

    loop = asyncio.get_event_loop()
    [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload, config)))
    sys.stdout.write(pgt.outputParse(result))


@run.command()
@click.option('--file', '-f', 'fileIn', default="",
              help="Input image-PDF file")
def process(fileIn):
    """
    PARSE
    Parse Image PDF file, output resulting text.
    (combines Extract and Ocr commands)
    """

    dirPath = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(dirPath, fileIn)
    outDir = os.getcwd()

    with pgt.pdf2png(config, filePath, outDir) as (taskid, path):

        payload = []
        for fname in os.listdir(path):
            order = int(fname[3:5])
            fpath = os.path.join(path, fname)
            payload.append((order, fpath))

        loop = asyncio.get_event_loop()
        [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload, config)))

    sys.stdout.write(pgt.outputParse(result))


@run.command()
def benchmark():
    """
    Run a quick platform benchmark
    """
    dirPath = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(dirPath, './resources/test_fr_7_img.pdf')
    outDir = os.getcwd()
    Score = lambda x: math.floor(7 / (time.time() - x) * 100)

    starttime = time.time()
    config['ocr']['workers'] = 1
    with pgt.pdf2png(config, filePath, outDir) as (taskid, path):
        payload = []
        for fname in os.listdir(path):
            order = int(fname[3:5])
            fpath = os.path.join(path, fname)
            payload.append((order, fpath))

        loop = asyncio.get_event_loop()
        [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload, config)))

    worker1_time = Score(starttime)

    starttime = time.time()
    config['ocr']['workers'] = 2
    with pgt.pdf2png(config, filePath, outDir) as (taskid, path):
        payload = []
        for fname in os.listdir(path):
            order = int(fname[3:5])
            fpath = os.path.join(path, fname)
            payload.append((order, fpath))

        loop = asyncio.get_event_loop()
        [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload, config)))

    worker2_time = Score(starttime)

    starttime = time.time()
    config['ocr']['workers'] = 'auto'
    with pgt.pdf2png(config, filePath, outDir) as (taskid, path):
        payload = []
        for fname in os.listdir(path):
            order = int(fname[3:5])
            fpath = os.path.join(path, fname)
            payload.append((order, fpath))

        loop = asyncio.get_event_loop()
        [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload, config)))

    workera_time = Score(starttime)

    sys.stdout.write(f"""
    1 Worker score : {worker1_time}
    2 Worker score : {worker2_time}
    Auto Worker score : {workera_time}

    Final: {int((worker1_time + worker2_time + workera_time)/3)}
    """)
    # print(worker3_time)


if __name__ == "__main__":
    run()
