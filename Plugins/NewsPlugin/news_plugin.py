import requests
import time
import json
from base_plugin import BasePlugin


# TODO: add 'about' feature to get topical news
class NewsPlugin(BasePlugin):

    def __init__(self):
        self.name = 'NewsPlugin'
        self.COMMAND_HOOK_DICT = {'get_news': ['get me the news', 'give me the news',
                                               'get me news', 'get the news', 'get news']
                                  }
        self.MODIFIERS = {'get_news': {'by': ['by', 'buy', 'bye']}}
        super().__init__(name=self.name,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def get_news(self):
        API_KEY = self.config_obj.environment_variables[self.name]['API_KEY']
        if self.command_dict['modifier'] == 'by':
            # a desired source is supplied
            source = self.command_dict['postmodifier']
            source = source.replace(' ', '-')
        else:
            # make Reuters the default news source
            source = 'reuters'
        # make the API call through newsapi.org with user's api key
        response = requests.get(r'https://newsapi.org/v1/articles?source='+source+'&sortBy=latest&apiKey='+str(API_KEY))
        response = json.loads(response.text)
        try:
            # get the first 5 articles
            articles = response['articles'][:5]
        except KeyError:
            self.vocalize('sorry, I do not recognize that source')
            return

        # read a short summary of the articles
        article_urls = []
        for i, article in enumerate(articles):
            article_urls.append(article['url'])
            self.vocalize('Article number {}'.format(i+1))
            self.vocalize(article['description'])
            time.sleep(0.5)

        # TODO: Figure out how to implement betas



        '''
        article_list = []
        for article in response:
            article_dict = {'headline': article['description'], 'url': article['url']}
            article_list.append(article_dict)

        for i, articles in enumerate(article_list):
            #vocalize('Article number '+str(i+1))
            #vocalize(articles['headline'])
            print(i)
            time.sleep(0.5)
        # TODO: figure out how to support beta plugins efficiently
        #vocalize('Would you like me to open any of these?')
        #answer = self.listener().listen_and_convert()
        answer = self.get_command()
        print(answer)
        #beta = OpenArticleBeta(answer, article_list)
        #beta.function_handler()
        '''