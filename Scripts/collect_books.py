# Collect books from the Gutenberg Project as raw text for model training


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
    parser.add_argument('--start_id', default=0, type=int, help='Book id to start iteration on')
    args = parser.parse_args()
    collect(args)


def collect(args):
    pbar = tqdm(total=(args.max_id-args.start_id), unit=' Book IDs')
    count = args.start_id
    while count < args.max_id:
        r = requests.get('https://www.gutenberg.org/files/{c}/{c}-0.txt'.format(c=count))
        if r.status_code != 200:
            count += 1
            pbar.update(1)
        else:
            soup = BeautifulSoup(r.content, 'html5lib')
            text = soup.text
            paragraphs = []
            lines = []
            for line in text.split('\n'):
                if len(line) <= 1:
                    paragraphs.append(lines)
                    lines = []
                else:
                    lines.append(line)
            # cut out the intro and license
            paragraphs = paragraphs[50:-100]
            # replace the new line splits with a space so each entry is one big line
            paragraphs = [' '.join(p) for p in paragraphs]
            for paragraph in paragraphs:
                # make sure all new lines are gone
                paragraph = paragraph.replace('\n', '')
                # remove content between parentheses
                paragraph = re.sub(r'\([^()]*\)', '', paragraph)
                # remove non ascii
                paragraph = re.sub(r'[^\x00-\x7f]', '', paragraph)
                # split on punctuation
                line_list = re.split('(?<=[.!?]) +', paragraph)
                clean_line_list = []
                for line in line_list:
                    # keep lines that start with uppercase letter
                    try:
                        if not line[0].isupper():
                            line = ''
                    except IndexError:
                        line = ''
                    # now make all lowercase
                    line = line.lower()
                    # throwout any chapter headings
                    if line.startswith('chapter'):
                        line = ''
                    # ensure single space
                    line = ' '.join([l for l in line.split() if l != ' '])
                    # remove any other  distraction chars
                    line = ''.join([l for l in line if l.isalpha() or l == ' '])
                    if line != '':
                        clean_line_list.append(line)
                # write to file followed by newline to indicate paragraph separation
                with open(os.path.join(args.data_dir, 'book_paragraphs.txt'), 'a') as f:
                    for clean_line in clean_line_list:
                        f.write(clean_line+'\n')
                    f.write('\n')
            count += 1
            pbar.update(1)
    pbar.close()


if __name__ == "__main__":
    main()
