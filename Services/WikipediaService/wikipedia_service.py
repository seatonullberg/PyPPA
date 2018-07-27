from base_service import BaseService


class WikipediaService(BaseService):

    def __init__(self):
        self.name = 'WikipediaService'
        self.input_filename = 'wikipedia_service.in'
        self.output_filename = 'wikipedia_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
