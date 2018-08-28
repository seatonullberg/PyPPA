from base_service import BaseService


class FlaskService(BaseService):

    def __init__(self):
        self.name = 'FlaskService'
        self.input_filename = 'flask_params.p'
        self.output_filename = 'flask_service.out'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def active(self):
        pass
