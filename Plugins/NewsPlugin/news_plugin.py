import requests
import time
import json
from Speaker import vocalize
from Plugins.base_plugin import BasePlugin
from private_config import NEWS_API_KEY
from Plugins.NewsPlugin.open_article_beta import OpenArticleBeta


# TODO: add 'about' feature to get topical news
class PyPPA_NewsPlugin(BasePlugin):

    def __init__(self, command):
        self.query = None
        self.COMMAND_HOOK_DICT = {'get_news': ['get me the news', 'give me the news',
                                               'get me news', 'get the news', 'get news']
                                  }
        self.MODIFIERS = {'get_news': {'by': ['by', 'buy', 'bye']}}
        super().__init__(command=command,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def function_handler(self, args=None):
        # default news source is Reuters
        self.query = 'reuters'
        # check for the modifier
        # will need to change if other modifiers are added
        if self.command_dict['modifier'] != '':
            # assume the postmodifer is the query in this case
            # 'get the news by *bloomberg*'
            self.query = self.command_dict['postmodifier']
        self.get_news_by_source()

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
        answer = self.listener().listen_and_convert()
        beta = OpenArticleBeta(answer, article_list)
        beta.function_handler()

        self.isBlocking = False
