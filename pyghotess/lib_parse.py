import os
import uuid
import asyncio
import logging
import shutil
import subprocess
from contextlib import contextmanager

logger = logging.getLogger(__name__)


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

    tempPath = os.path.join(outDir, taskid)
    os.mkdir(tempPath)

    subprocess.run([
        'gs',
        '-q',
        '-sDEVICE=png16m',
        '-dTextAlphaBits=4',
        f'-o{tempPath}/gs-%02d.png',
        '-dNOPAUSE',
        '-r200',
        filePath]
    )

    try:
        yield (taskid, tempPath)

    finally:
        if cleanUp:
            shutil.rmtree(tempPath)


async def worker(name, queue_in, queue_out):
    while True:
        order, fpath = await queue_in.get()
        logger.debug('Worker %s starting on file %s', name, order)
        cmd = [
            'tesseract',
            '--psm','4',
            '-l', 'fra',
            '--dpi', '200',
            fpath,
            'stdout',
        ]
        await asyncio.sleep(1)

        proc = await asyncio.create_subprocess_shell(
                ' '.join(cmd),
                stdout=asyncio.subprocess.PIPE)
        # result = subprocess.run(cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        queue_out.put_nowait((order, stdout.decode()))
        queue_in.task_done()


async def process(payloads):
    queue_in = asyncio.Queue()
    queue_out = asyncio.Queue()

    logger.debug('Filling queue in')
    for payload in payloads:
        queue_in.put_nowait(payload)

    logger.debug('Creating tasks')
    tasks = []
    for i in range(8):
        task = asyncio.create_task(worker(f'w-{i}', queue_in, queue_out))
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


