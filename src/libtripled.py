#!/bin/env python

import logging, zmq, pickle

log = logging.getLogger('tripled.libtripled') 

class tripled:
    def __init__(self, master):
        self.context = zmq.Context()
        self.workers = {}
        self.master = self.get_master(master)

    def get_master(self, master):
        socket = self.context.socket(zmq.REQ)
        uri = 'tcp://%s:1337' % (master)
        log.debug('master connect string[%s]', uri)
        socket.connect(uri)
        return socket

    def get_worker(self, worker):
        if worker in self.workers:
            log.debug('using cached worker connection')
            worker = self.workers[worker]
        else:
            socket = self.context.socket(zmq.REQ)
            uri = 'tcp://%s:8008' % (worker)
            log.debug('worker connect string[%s]', uri)
            socket.connect(uri)
            self.workers[worker] = socket
            worker = self.workers[worker]
        return worker 

    def read_file(self, path):
        self.master.send(pickle.dumps(('read', path)))
        blocks = pickle.loads(self.master.recv())
        log.debug('blocks: %s', blocks)
        deserialized_blocks = [pickle.loads(block) for block in blocks]
        log.debug('deserialized: %s', deserialized_blocks)
        return deserialized_blocks 

    def write_block(self, path, block, data):
        self.master.send(pickle.dumps(('write', path, block)))
        details = pickle.loads(self.master.recv())
        self.worker_write_block(details[0], details[1], data)

    def read_block(self, worker, path):
        worker = self.get_worker(worker)
        worker.send(pickle.dumps(('read',path)))
        return pickle.loads(worker.recv())

    def worker_write_block(self, worker, path, data):
        log.debug('writing[%s] to worker[%s]' % (path, worker))
        worker = self.get_worker(worker)
        log.debug('got socket...writing data[%d]' % (len(data)))
        worker.send(pickle.dumps(('write', path, data)))
        log.debug('sent message...')
        return pickle.loads(worker.recv())

if __name__ == '__main__':
    print 'This is a library of client functions.'
