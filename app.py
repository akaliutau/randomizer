import argparse
import logging
import os
import psutil
import random
import uuid
from pathlib import Path

import colorlog
from flask import Flask, jsonify, request

# Writable directory
WRITE_DIR = '/tmp'

# File for readiness probe
READY_FILE = Path(os.path.join(WRITE_DIR, 'randomizer-ready'))

app = Flask(__name__)

health_status = True
buffer = []

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s %(asctime)s [%(filename)s] %(levelname)s %(message)s',
    log_colors={
        'INFO': 'black',
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red'
    }
))

log = app.logger
log.addHandler(handler)
log.setLevel(logging.DEBUG)


def readiness_lock_file(create: bool = True) -> None:
    if create:
        log.info("creating lock file for readiness probe: %s", READY_FILE)
        if not Path(READY_FILE).exists():
            os.close(
                os.open(READY_FILE, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            )
    else:
        os.remove(READY_FILE)


def read_all(filename: Path) -> str:
    if filename.exists():
        with open(filename, 'r') as file:
            data = file.read()
            return data


class Properties:

    def __init__(self):
        self.version = '1.0'
        self.id = str(uuid.uuid1())
        self.logFile = os.environ.get('LOG_FILE')
        self.logUrl = os.environ.get('LOG_URL')
        self.port = os.environ.get('PORT', 8080)
        self.seed = 0


properties = Properties()
random_gen = random.Random()
random_gen.seed(properties.seed)

process = psutil.Process()


@app.route('/')
def random():
    return jsonify({
        'id': properties.id,
        'version': properties.version,
        'random': random_gen.random()
    })


@app.route('/memory-loader')
def memory_eater():
    size = request.args.get('mb', 0) or 0
    global buffer
    log.info("creating buffer in %s [MB]", size)
    buffer = [random_gen.random() for _ in range(int(size) * 1024 * 1024)]
    return {'allocated_mb' : size}, 200


@app.route('/toggle-live')
def toggle_live():
    global health_status
    health_status = not health_status
    return jsonify(health_value=health_status), 200


@app.route('/toggle-ready')
def toggle_ready():
    readiness_lock_file(not READY_FILE.exists())
    return '', 200


@app.route('/health')
def health():
    if health_status:
        resp = jsonify(health="healthy")
        resp.status_code = 200
    else:
        resp = jsonify(health="unhealthy")
        resp.status_code = 500

    return resp


@app.route('/info')
def sys_info():
    env = os.environ
    stat = {
        'id': properties.id,
        'version': properties.version,
        'memory_used': process.memory_info().rss,
        'cpus': process.cpu_num(),
        'logFile': properties.logFile,
        'logUrl': properties.logUrl,
        'seed': properties.seed,
        'port': properties.port
    }

    # collect data from Downward API environment
    if env.get('POD_ID'):
        stat['POD_ID'] = env.get('POD_ID')
    if env.get('NODE_NAME'):
        stat['NODE_NAME'] = env.get('NODE_NAME')

    # collect data from kubelet fs
    pod_info = Path('/pod_info')
    if pod_info.exists() and pod_info.is_dir():
        for meta_data in ['labels', 'annotations']:
            f = Path(pod_info, meta_data)
            stat[f.name] = read_all(Path(pod_info, meta_data))
    return jsonify(stat), 200


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates random numbers')
    parser.add_argument('-l', '--lines', help='number of lines', default=20, required=False)

    args = vars(parser.parse_args())

    readiness_lock_file()
    app.run(host='0.0.0.0', port=properties.port)
