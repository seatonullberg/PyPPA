import wikipedia
import time
import numpy as np
import re


class WikiCollector(object):

    def __init__(self):
        self.FREQUENCY = 3600   # run hourly

    def startup(self):
        # run all functions that are not private or startup
        funcs = dir(WikiCollector)
        funcs.remove('startup')
        for func in funcs:
            if not str(func).startswith('_'):
                getattr(WikiCollector, func)(self)
        # sleep for delay time and then redo the tasks
        time.sleep(self.FREQUENCY)
        self.startup()

    def collect_articles(self):
        while True:
            past_titles = [t.replace('\n','') for t in open('title_log.txt', 'r').readlines()]
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

            with open('wiki_sections.txt', 'a') as f:
                for sections in section_content:
                    for sentences in section_content[sections]:
                        f.write(sentences+'\n')
                    f.write('\n')
            with open('title_log.txt', 'a') as f:
                f.write(article.title+'\n')

            print(article.title)


if __name__ == "__main__":
    w = WikiCollector()
    w.startup()
