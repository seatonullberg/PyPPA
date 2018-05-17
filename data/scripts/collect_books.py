import requests
from bs4 import BeautifulSoup
from private_config import DATA_DIR
import re

count = 0
while True:
    r = requests.get('https://www.gutenberg.org/files/{c}/{c}-0.txt'.format(c=count))
    if r.status_code != 200:
        print('Page not available: {}'.format(count))
        count += 1
    else:
        soup = BeautifulSoup(r.content, 'html5lib')
        text = soup.text
        paragraphs = text.split('\n\n')
        # cut out the intro and license
        paragraphs = paragraphs[25:-100]
        for line in paragraphs:
            # remove content between parentheses
            line = re.sub(r'\([^()]*\)', '', line)
            # remove non ascii
            line = re.sub(r'[^\x00-\x7f]', '', line)
            # convert new lines to spaces
            line = ' '.join(line.split('\n'))
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
            with open(DATA_DIR+'/text/books/book_paragraphs.txt', 'a') as f:
                for sentence in line:
                    f.write(sentence+'\n')
                f.write('\n')
        count += 1

