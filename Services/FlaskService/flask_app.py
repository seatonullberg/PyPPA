from flask import Flask


class FlaskApp(Flask):

    def __init__(self, functions, name, address):
        self.functions = functions
        self.address = address
        super().__init__(name)
        self.run(host=address['host'], port=address['port'])
