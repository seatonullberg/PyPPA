'''
Collect books from the Gutenberg Project as raw text for model training
'''
# TODO: Revise line cleaning
import requests
from bs4 import BeautifulSoup
import re
import os
import argparse
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default=None, help='Path to where book text will be stored')
    parser.add_argument('--max_id', default=60000, type=int, help='Book id to iterate to')
    args = parser.parse_args()
    collect(args)


def collect(args):
    pbar = tqdm(total=args.max_id, unit=' Book IDs')
    count = 0
    while count < args.max_id:
        r = requests.get('https://www.gutenberg.org/files/{c}/{c}-0.txt'.format(c=count))
        if r.status_code != 200:
            count += 1
            pbar.update(1)
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
                with open(os.path.join(args.data_dir, 'book_paragraphs.txt'), 'a') as f:
                    for sentence in line:
                        f.write(sentence + '\n')
                    f.write('\n')
            count += 1
            pbar.update(1)
    pbar.close()


if __name__ == "__main__":
    main()
