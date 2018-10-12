import requests
import time
import json

from Plugins import base


class NewsPlugin(base.Plugin):

    def __init__(self):
        """
        Collects recent news stories from newsapi.org and reads them aloud
        """
        self.name = 'NewsPlugin'
        self.command_hooks = {self.get_news: ['get me the news', 'give me the news',
                                              'get me news', 'get the news', 'get news']
                              }
        self.modifiers = {self.get_news: {'by': ['by', 'buy', 'bye']}}
        super().__init__(name=self.name,
                         command_hooks=self.command_hooks,
                         modifiers=self.modifiers)

    def get_news(self):
        """
        Make the api call and include 'source' as a user option through modifiers
        """
        api_key = self.environment_variable('API_KEY')
        if self.command.modifier == 'by':
            # a desired source is supplied
            source = self.command.postmodifier
            source = source.replace(' ', '-')
        else:
            # make Reuters the default news source
            source = 'reuters'
        # make the API call through newsapi.org with user's api key
        response = requests.get('https://newsapi.org/v1/articles?source={}&sortBy=latest&apiKey={}'.format(source,
                                                                                                           api_key))
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
            self.vocalize('Article number {}'.format(i + 1))
            if article['description'] is None:
                self.vocalize('does not have a description')
            else:
                self.vocalize(article['description'])
            time.sleep(0.5)

        self.sleep()

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