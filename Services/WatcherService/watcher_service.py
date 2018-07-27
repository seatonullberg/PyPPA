from base_service import BaseService


class WatcherService(BaseService):

    def __init__(self):
        self.name = 'WatcherService'
        self.input_filename = 'watcher_service.in'
        self.output_filename = 'watcher_service.out'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
