import webbrowser
from flask import Flask
import time
app = Flask(__name__)

webbrowser.open(r'http://127.0.0.1:5000/')
time.sleep(2)
webbrowser.open(r'http://127.0.0.1:5000/')


@app.route("/")
def hello():
    return "Hello World!"
