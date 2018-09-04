import pickle
from base_service import BaseService
from flask import Flask, render_template
from threading import Thread
import os
import time
app = Flask("FlaskService")


@app.route('/<name>')
def test_method(name):
    html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(name))
    with open(html_path) as f:
        html = f.read()
    return html


class FlaskService(BaseService):

    def __init__(self, host='0.0.0.0', port=7000):
        self.name = 'FlaskService'
        self.input_filename = 'flask_service_input.p'
        self.output_filename = 'flask_service.out'
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
        self.host = host
        self.port = port

    def mainloop(self):
        ##### CHANGES FROM BASE
        # dynamically add routes and files for all plugins
        for p in self.config_obj.plugins:
            html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(p))
            with open(html_path, 'w') as f:
                f.write(p)
            '''
            method_str = "def {plugin}(self):\n\treturn render_template({plugin}.html)".format(plugin=p)
            method = exec(method_str)
            setattr(self, p, method)
            app.route('/{}'.format(p))(self.test_method)
            '''
        # start the flask app
        Thread(target=app.run, args=[self.host, self.port]).start()
        ##### END CHANGES

        # keep the service running continuously
        while True:
            if os.path.isfile(self.input_filename):
                # wait for any desired response delay
                # TODO: do this without delays
                # it currently exists because some files
                # can trigger True before the content is ready
                time.sleep(self.delay)
                self.active()
                # clean up to prevent perpetual active loop
                os.remove(self.input_filename)
            else:
                self.default()

    def active(self):
        args_dict = pickle.load(open(self.input_filename, 'rb'))
        _name = args_dict['name']
        _html = args_dict['html']
        html_path = os.path.join('Services', 'FlaskService', 'templates', '{}.html'.format(_name))
        with open(html_path, 'w') as f:
            f.write(_html)
        test_method(_name)
