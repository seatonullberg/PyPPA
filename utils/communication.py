class Request(object):
    """
    Base class used to make inter-process communications more simple
    - packages use these Request types to send and recieve data from one another
    - App object coordinates the interprocess interaction
    """

    def __init__(self, send_name, return_name=None):
        self.outgoing = None  # indicate if this is the initial request (True) or response to request (False)
        self.send_name = send_name
        self.return_name = return_name

    def send(self, queue):
        """
        Sends the request as client
        :param queue: (utils.parallelization_utils.TwoWayProcessQueue)
        """
        self.outgoing = True
        queue.client_put(self)

    def respond(self, queue):
        """
        Responds to request as client
        :param queue: (utils.parallelization_utils.TwoWayProcessQueue)
        """
        self.outgoing = False
        if self.return_name is not None:
            queue.client_put(self)


class PluginRequest(Request):
    """
    Use when:
             making another plugin active
    """

    def __init__(self, plugin_name, command_string, return_name=None):
        super().__init__(plugin_name, return_name)
        self.send_name = plugin_name
        self.return_name = return_name
        self.command_string = command_string


class DataRequest(Request):
    """
    Use when:
             requesting behavior or data from a package
    """

    def __init__(self, send_name, return_name, data):
        super().__init__(send_name, return_name)
        self.send_name = send_name
        self.return_name = return_name
        self.data = data


class CommandAcceptanceRequest(Request):
    """
    Use when:
             testing a command's validity in another plugin
    """

    def __init__(self, plugin_name, return_name, command_string):
        super().__init__(plugin_name, return_name)
        self.send_name = plugin_name
        self.return_name = return_name
        self.command_string = command_string
        self.accepts = None


class CacheRequest(Request):
    """
    Use when:
             reading or writing a pickle file
    """
    # TODO
