import requests
import time
import json
from Speaker import vocalize
from base_plugin import BasePlugin
from Plugins.NewsPlugin.open_article_beta import OpenArticleBeta


# TODO: add 'about' feature to get topical news
class NewsPlugin(BasePlugin):

    def __init__(self):
        self.name = 'news_plugin'
        self.COMMAND_HOOK_DICT = {'get_news': ['get me the news', 'give me the news',
                                               'get me news', 'get the news', 'get news']
                                  }
        self.MODIFIERS = {'get_news': {'by': ['by', 'buy', 'bye']}}
        super().__init__(name=self.name,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def get_news(self):
        NEWS_API_KEY = self.config_obj.environment_variables[self.name]['NEWS_API_KEY']
        if self.command_dict['modifier'] != '':
            # a desired source is supplied
            source = self.command_dict['postmodifier']
        else:
            # make Reuters the default news source
            source = 'reuters'

        response = requests.get(
            r'https://newsapi.org/v1/articles?source='+source+'&sortBy=latest&apiKey='+str(NEWS_API_KEY))
        response = json.loads(response.text)
        try:
            response = response['articles']
        except KeyError:
            response = requests.get(
                r'https://newsapi.org/v1/articles?source='+source+'&sortBy=latest&apiKey='+str(NEWS_API_KEY))
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
        # TODO: figure out how to support beta plugins efficiently
        vocalize('Would you like me to open any of these?')
        answer = self.listener().listen_and_convert()
        beta = OpenArticleBeta(answer, article_list)
        beta.function_handler()
