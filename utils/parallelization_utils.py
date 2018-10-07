import multiprocessing


class TwoWayProcessQueue(object):
    """
    Convenience object to allow two-way data transfer between processes
    - first in == first out
    """
    def __init__(self):
        self._server_queue = multiprocessing.Queue()
        self._client_queue = multiprocessing.Queue()

    def server_put(self, obj):
        """
        Appends obj to the server queue
        :param obj: any object
        """
        self._server_queue.put(obj)

    def server_get(self):
        """
        Pops obj from the server queue
        :return: obj from queue
        """
        return self._server_queue.get()

    def server_empty(self):
        """
        Checks if the server queue is empty
        :return: (bool)
        """
        return self._server_queue.empty()

    def client_put(self, obj):
        """
        Appends obj to the client queue
        :param obj: any object
        """
        self._client_queue.put(obj)

    def client_get(self):
        """
        Pops obj from the client queue
        :return: obj from queue
        """
        return self._client_queue.get()

    def client_empty(self):
        """
        Checks if the client queue is empty
        :return: (bool)
        """
        return self._client_queue.empty()
