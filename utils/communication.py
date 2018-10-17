class Link(object):
    """
    Base class for inter-package communication
    """

    def __init__(self, producer, consumer):
        self.producer = producer
        self.consumer = consumer
        self.fields = {}
        self.complete = False
        self.key = None


class PluginLink(Link):

    def __init__(self, producer, consumer, command_string):
        super().__init__(producer, consumer)
        self.fields['command_string'] = command_string


class DataLink(Link):

    def __init__(self, producer, consumer, input_data):
        super().__init__(producer, consumer)
        self.fields['input_data'] = input_data
        self.fields['output_data'] = None


class AcceptanceLink(Link):

    def __init__(self, producer, consumer, command_string):
        super().__init__(producer, consumer)
        self.fields['command_string'] = command_string
        self.fields['result'] = None
