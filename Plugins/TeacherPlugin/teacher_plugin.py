import wikipedia
import requests
from Speaker import vocalize
from bs4 import BeautifulSoup
from base_plugin import BasePlugin


# TODO: chunk the instructions for more efficient vocalization
class TeacherPlugin(BasePlugin):

    def __init__(self):
        self.name = 'teacher_plugin'
        self.COMMAND_HOOK_DICT = {'teach_me': ['teach me about', 'teach me']}
        self.MODIFIERS = {'teach_me': {'how_to': ['how too', 'hot to', 'hot too', 'how to']}}
        super().__init__(command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS,
                         name=self.name)

    def teach_me(self):
        if self.command_dict['modifier'] == 'how_to':
            self.scrape_wikihow(self.command_dict['postmodifier'])
        else:
            self.basic_teach(self.command_dict['premodifier'])
        # remain after use
        self.pass_and_terminate(name='sleep_plugin',
                             cmd='sleep')

    def basic_teach(self, query):
        try:
            summary = wikipedia.summary(query, auto_suggest=True)
            print(summary)
            #vocalize('ok, this is what i know about '+query)
            #vocalize(summary)
        except wikipedia.DisambiguationError:
            print('could you be more specific')
            #vocalize('could you be more specific?')

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
            # vocalize('sorry, i do not know how to ' + query)
            print('sorry, I do not know how to '+query)
        else:
            reading_text = ' '.join(reading_text)
            print(reading_text)
            # vocalize('ok, this is how to ' + query)
            # vocalize(reading_text)
