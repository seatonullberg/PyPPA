import wikipedia
import requests
from bs4 import BeautifulSoup

from Plugins import base


class TeacherPlugin(base.Plugin):

    def __init__(self):
        """
        Scrapes wikipedia or wikihow to provide information on a requested topic
        """
        self.name = 'TeacherPlugin'
        self.command_hooks = {self.teach_me: ['teach me about', 'teach me']}
        self.modifiers = {self.teach_me: {'how_to': ['how too', 'hot to', 'hot too', 'how to']}}
        super().__init__(command_hooks=self.command_hooks,
                         modifiers=self.modifiers,
                         name=self.name)

    def teach_me(self):
        if self.command.modifier == 'how_to':
            self.scrape_wikihow(self.command.postmodifier)
        else:
            self.basic_teach(self.command.premodifier)

        self.sleep()

    def basic_teach(self, query):
        try:
            summary = wikipedia.summary(query, auto_suggest=True)
            self.vocalize('ok, this is what i know about '+query)
            print(summary)
            self.vocalize(summary)
        except wikipedia.DisambiguationError:
            self.vocalize('could you be more specific?')

    def scrape_wikihow(self, query):
        r = requests.get(r'https://www.wikihow.com/'+query)

        readable = r.text
        soup = BeautifulSoup(readable, 'html.parser')

        reading_text = []
        for paragraphs in soup.find_all('div', {'class': 'step'}):
            p_text = paragraphs.text
            for scripts in paragraphs.find_all('script'):
                s_text = scripts.text
                p_text = p_text.replace(s_text, '')
            reading_text.append(p_text)

        if len(reading_text) < 1:
            self.vocalize('sorry, i do not know how to ' + query)
        else:
            reading_text = ' '.join(reading_text)
            self.vocalize('ok, this is how to ' + query)
            print(reading_text)
            self.vocalize(reading_text)
