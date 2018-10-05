from collections import deque


class TwoWayQueue(object):
    """
    Convenience object to allow two-way data transfer between threads
    - first in == first out
    """
    def __init__(self):
        self._server_queue = deque()
        self._client_queue = deque()

    def server_put(self, obj):
        """
        Appends obj to the server queue
        :param obj: any object
        """
        self._server_queue.append(obj)

    def server_get(self):
        """
        Pops obj from the server queue
        :return: obj from queue
        """
        return self._server_queue.popleft()

    def server_empty(self):
        """
        Checks if the server queue is empty
        :return: (bool)
        """
        if len(self._server_queue) == 0:
            return True
        else:
            return False

    def client_put(self, obj):
        """
        Appends obj to the client queue
        :param obj: any object
        """
        self._client_queue.append(obj)

    def client_get(self):
        """
        Pops obj from the client queue
        :return: obj from queue
        """
        return self._client_queue.popleft()

    def client_empty(self):
        """
        Checks if the client queue is empty
        :return: (bool)
        """
        if len(self._client_queue) == 0:
            return True
        else:
            return False
