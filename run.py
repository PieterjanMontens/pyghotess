#!/usr/bin/env python3
import click
import sys
import logging
import os
import asyncio
import pyghotess as pgt

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())

config = {
}


@click.group()
@click.option('--debug', '-d', 'debug', default=False)
def run(debug):
    if debug:
        logger.setLevel(logging.getLevelName('DEBUG'))


@run.command()
@click.option('--file', '-f', 'fileIn', default="")
@click.option('--out-dir', '-o', 'outDir', default="")
def extract(fileIn, outDir):
    dirPath = os.path.dirname(os.path.realpath(__file__))
    filePath = os.path.join(dirPath, fileIn)
    if outDir == "":
        outDir = os.getcwd()
    with pgt.pdf2png(config, filePath, outDir=outDir, cleanUp=False) as (taskid, path):
        logger.info('Extracted PDF file to directory:/n %s', path)
        sys.stdout.write(path)


@run.command()
@click.option('--dir', 'directory', default="")
def ocr(directory):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    work_path = os.path.join(dir_path, directory)

    payload = []
    for fname in os.listdir(directory):
        order = int(fname[3:5])
        fpath = os.path.join(work_path, fname)
        payload.append((order, fpath))

    loop = asyncio.get_event_loop()
    [result] = loop.run_until_complete(asyncio.gather(pgt.process(payload)))
    sys.stdout.write(pgt.outputParse(result))


if __name__ == "__main__":
    run()
