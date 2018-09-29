import pickle
from flask import Flask
from threading import Thread
import os
from Services import base
# i apologize for the gross flask initialization here
# not sure how to fix
app = Flask("FlaskService")


@app.route('/<name>')
def test_method(name):
    html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(name))
    try:
        with open(html_path) as f:
            html = f.read()
    except FileNotFoundError as e:
        return str(e)
    else:
        return html


class FlaskService(base.Service):

    def __init__(self,):
        self.name = 'FlaskService'
        self.input_filename = 'flask_service_input.p'
        self.output_filename = 'flask_service.out'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def mainloop(self):
        ##### CHANGES FROM BASE
        # add blank .html files for all plugins
        for p in self.config_obj.plugins:
            html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(p))
            with open(html_path, 'w') as f:
                f.write(p)
        # start the flask app
        host = self.config_obj.environment_variables[self.name]['HOST']
        port = self.config_obj.environment_variables[self.name]['PORT']
        port = int(port)
        Thread(target=app.run, args=[host, port]).start()
        ##### END CHANGES
        super().mainloop()

    def active(self):
        args_dict = pickle.load(open(self.input_filename, 'rb'))
        _name = args_dict['name']
        _html = args_dict['html']
        html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(_name))
        with open(html_path, 'w') as f:
            f.write(_html)
        test_method(_name)
