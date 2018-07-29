from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from multiprocessing import Process
import time
from flask import Flask
app = Flask("name")


def base():
    return "hello world"

### THIS IS THE ALTERNATIVE TO THE DECORATOR SYNTAX
app.route('/')(base)
### ALLOWS THE FLASKAPP OBJECT TO BE PROGRAMATICALLY GENERATED
# plugin passes in a list of functions and this logic is applied where 'base' is a passed in function


def run(url):
    options = webdriver.chrome.options.Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-default-apps')
    driver = webdriver.Chrome(
                executable_path='/usr/local/bin/chromedriver',
                options=options,
                )
    driver.get(url)
    time.sleep(3)
    driver.get("http://localhost:5000")
    time.sleep(3)
    driver.quit()


if __name__ == "__main__":
    Process(target=app.run, args=(['0.0.0.0', 5000])).start()
    allurls = ['https://github.com/',
               'https://docs.python.org/3/library/webbrowser.html'
               ]
    for urls in allurls:
        p = Process(target=run, args=(urls,))
        p.start()
