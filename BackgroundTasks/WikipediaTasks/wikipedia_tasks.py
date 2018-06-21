# TODO: Make use of the log function
import wikipedia
import numpy as np
import re
import os
from base_background_task import BaseBackgroundTask


class WikipediaTasks(BaseBackgroundTask):

    def __init__(self):
        self.name = 'wikipedia_tasks'
        # this task is already an infinite loop so the delay has no effect
        #TODO: might change this later
        self.delays = [(self.collect_articles, 0)]
        super().__init__(delays=self.delays,
                         name=self.name)

    def collect_articles(self):
        '''
        Collect Wikipedia articles at random and store the sentences in sections as raw text data
        :return: None (write data to file)
        '''
        DATA_DIR = self.config_obj.environment_variables['__BASE__']['DATA_DIR']
        title_log_path = [DATA_DIR, 'background_logs', 'Wikipedia', 'title_log.txt']
        wiki_sections_path = [DATA_DIR, 'text', 'Wikipedia', 'wiki_sections.txt']
        while True:
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
                    continue
                try:
                    article = wikipedia.page(title=e.options[seed])
                except wikipedia.DisambiguationError:
                    # if it happens again just ignore that title
                    continue
                except wikipedia.PageError:
                    print('Could not find a page for {}'.format(title))
                    continue
                except wikipedia.WikipediaException:
                    # wikipedia.exceptions.WikipediaException: An unknown error occured:
                    # "The "search" parameter must be set.". Please report it on GitHub!
                    continue
            except wikipedia.PageError:
                print('Could not find a page for {}'.format(title))
                continue
            except wikipedia.WikipediaException:
                # wikipedia.exceptions.WikipediaException: An unknown error occured:
                # "The "search" parameter must be set.". Please report it on GitHub!
                continue
            if article.title in past_titles:
                continue
            if article.title.startswith('List of'):
                continue
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
            print(article.title)