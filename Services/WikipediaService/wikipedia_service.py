import wikipedia
import numpy as np
import re
import os
from Services import base


class WikipediaService(base.Service):

    def __init__(self):
        self.name = 'WikipediaService'
        self.input_filename = 'wikipedia_service.in'
        self.output_filename = 'wikipedia_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def default(self):
        # get a wiki page every 5 seconds
        if self.clock.since_output > 5:
            self.collect_article()

    def collect_article(self):
        '''
        Collect Wikipedia articles at random and store the sentences in sections as raw text data
        :return: None (write data to file)
        '''
        DATA_DIR = self.config_obj.environment_variables['Base']['DATA_DIR']
        title_log_path = [DATA_DIR, 'background_logs', 'Wikipedia', 'title_log.txt']
        wiki_sections_path = [DATA_DIR, 'text', 'Wikipedia', 'wiki_sections.txt']
        past_titles = [t.replace('\n', '') for t in open(os.path.join('', *title_log_path), 'r').readlines()]
        title = wikipedia.random()
        try:
            article = wikipedia.page(title=title)
        except wikipedia.DisambiguationError as e:
            # occurs when multiple articles have same title
            try:
                seed = np.random.randint(0, len(e.options))
            except ValueError:
                # caused when there are no options
                return
            try:
                article = wikipedia.page(title=e.options[seed])
            except wikipedia.DisambiguationError:
                # if it happens again just ignore that title
                return
            except wikipedia.PageError:
                return
            except wikipedia.WikipediaException:
                # wikipedia.exceptions.WikipediaException: An unknown error occured:
                # "The "search" parameter must be set.". Please report it on GitHub!
                return
        except wikipedia.PageError:
            return
        except wikipedia.WikipediaException:
            # wikipedia.exceptions.WikipediaException: An unknown error occured:
            # "The "search" parameter must be set.". Please report it on GitHub!
            return
        if article.title in past_titles:
            return
        if article.title.startswith('List of'):
            return
        lines = [l for l in article.content.split('\n') if len(l.split()) > 0]
        forbidden_sections = ['References', 'External links', 'See also']
        section_content = {}
        current_section = 'Summary'
        for line in lines:
            if line.startswith('='):
                section = line.replace('=', '')
                section = section.strip()
                if section not in forbidden_sections:
                    current_section = section
                else:
                    break
            else:
                # remove content between parentheses
                line = re.sub(r'\([^()]*\)', '', line)
                # remove non ascii
                line = re.sub(r'[^\x00-\x7f]', '', line)
                # remove punctuation aside from endings
                line = ''.join([char for char in line if char.isalpha() or char in ['!', '?', '.', ' ']])
                # split on end punctuation
                line = re.split('(?<=[.!?]) +', line)
                # now remove the end punctuation
                line = [l.replace('!', '').replace('?', '').replace('.', '') for l in line]
                # keep sentences that start with uppercase letter
                try:
                    line = [l for l in line if l[0].isupper()]
                except IndexError:
                    line = ''
                # keep sentences of 2 words or greater
                line = [l for l in line if len(l.split()) > 1]
                # make all lowercase
                line = [l.lower() for l in line]
                section_content[current_section] = line

        with open(os.path.join('', *wiki_sections_path), 'a') as f:
            for sections in section_content:
                for sentences in section_content[sections]:
                    f.write(sentences + '\n')
                f.write('\n')
        with open(os.path.join('', *title_log_path), 'a') as f:
            f.write(article.title + '\n')
