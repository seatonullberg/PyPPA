import os
import pickle
from base_service import BaseService
from flask import Flask


class FlaskApp(Flask):

    def __init__(self, name, host, port):
        self.host = host
        self.port = port
        super().__init__(name)
        self.run(host=self.host, port=self.port)


class FlaskService(BaseService):

    def __init__(self):
        self.name = 'FlaskService'
        self.input_filename = 'flask_service_input.p'
        self.output_filename = 'flask_service.out'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
        self.app_dict = {}

    def make_app(self):
        args_dict = pickle.load(open(self.input_filename, 'rb'))
        # instantiate a flask app
        app = FlaskApp(name=args_dict['name'],
                       host=args_dict['host'],
                       port=args_dict['port'])
        self.app_dict[args_dict['name']] = app
        return app

    def active(self):
        args_dict = pickle.load(open(self.input_filename, 'rb'))
        # process html arg as html string literal
        if os.path.isfile(args_dict['html']):
            # process the html as a filepath
            with open(args_dict['html']) as f:
                html = ''.join(f.readlines())
        else:
            # process the html as a literal html string
            html = args_dict['html']

        # check if app has already been instantiated by the same name
        try:
            app = self.app_dict[args_dict['name']]
        except KeyError:
            app = self.make_app()
        render = lambda _html:  _html
        app.route('/{}'.format(args_dict['name']))(render(html))
