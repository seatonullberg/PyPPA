from queue import Queue


class TwoWayQueue(object):
    """
    Convenience object to allow two-way data transfer between threads
    """
    def __init__(self):
        self.server_queue = Queue()
        self.client_queue = Queue()
