import requests
import time
import json
from Speaker import vocalize
from floating_listener import listen_and_convert
from private_config import NEWS_API_KEY
from Plugins.NewsPlugin.open_article_beta import OpenArticleBeta

'''
TODO:
add topical search with 'about' function key
'''


class PyPPA_NewsPlugin(object):

    def __init__(self, command):
        self.command = command
        self.query = None
        self.COMMAND_HOOK_DICT = {'get the news': ['get me the news', 'give me the news', 'get me news', 'get the news']}
        self.FUNCTION_KEY_DICT = {'by': ['by', 'buy', 'bye']}
        self.isBlocking = True

    def function_handler(self, command_hook, spelling):
        for variations in self.FUNCTION_KEY_DICT['by']:
            if variations in self.command:
                self.query = self.command.replace(spelling, '')
                self.query = self.query.replace(variations, '')
                self.get_news_by_source()
                return

        self.query = 'reuters'
        self.get_news_by_source()

    def update_database(self):
        pass

    def get_news_by_source(self):
        response = requests.get(
            r'https://newsapi.org/v1/articles?source='+self.query+'&sortBy=latest&apiKey='+str(NEWS_API_KEY))
        response = json.loads(response.text)
        try:
            response = response['articles']
        except KeyError:
            self.query = self.query.split()
            self.query = '-'.join(self.query)
            response = requests.get(
                r'https://newsapi.org/v1/articles?source='+self.query+'&sortBy=latest&apiKey='+str(NEWS_API_KEY))
            response = json.loads(response.text)
            try:
                response = response['articles']
            except KeyError:
                vocalize('Sorry, I do not recognize that source')
                return

        response = response[:5]
        article_list = []
        for article in response:
            article_dict = {'headline': article['description'], 'url': article['url']}
            article_list.append(article_dict)

        for i, articles in enumerate(article_list):
            vocalize('Article number '+str(i+1))
            vocalize(articles['headline'])
            time.sleep(0.5)
        vocalize('Would you like me to open any of these?')
        answer = listen_and_convert()
        beta = OpenArticleBeta(answer, article_list)
        beta.function_handler()

        self.isBlocking = False
