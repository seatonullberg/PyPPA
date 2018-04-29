from utils.nlp_utils import convert_sentence_to_matrix
import sqlite3
import praw
import time
from praw.models import MoreComments
from bs4 import BeautifulSoup
import requests
import re
import os
import pickle
from Crypto.Hash import SHA256
from private_config import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT, REDDIT_USERNAME, DATA_DIR


class RedditBot(object):

    def __init__(self):
        self.FREQUENCY = 3600   # repeat every hour
        self.bot = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                               client_secret=REDDIT_SECRET,
                               user_agent=REDDIT_USER_AGENT)
        self.user = self.bot.redditor(REDDIT_USERNAME)

    def startup(self):
        # run all functions that are not private or startup
        funcs = dir(RedditBot)
        funcs.remove('startup')
        for func in funcs:
            if not str(func).startswith('_'):
                getattr(RedditBot, func)(self)
        # sleep for delay time and then redo the tasks
        time.sleep(self.FREQUENCY)
        self.startup()

    def _store_conversational_text(self, table_name, response_text):
        '''
        Adds conversational style text to the conversational db for future processing
        :param table_name: name of the sql table to add to (all alpha hex of the sentence that was used to make matrix)
        :param response_text: response to the sentence
        :return: None (stores data in db)
        '''
        conn = sqlite3.connect(DATA_DIR+'/conversational_text/conversational_text.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS {}(response TEXT, frequency INTEGER)'.format(table_name))
        cursor.execute('SELECT frequency FROM {} WHERE response=?'.format(table_name), [response_text])
        freq = cursor.fetchone()
        if freq is None:
            freq = 0
            cursor.execute('INSERT INTO {} (response, frequency) VALUES (?, ?)'.format(table_name),
                           [response_text, freq])
        else:
            freq = freq[0] + 1
            cursor.execute('UPDATE {} SET frequency=? WHERE response=?'.format(table_name), [freq, response_text])
        conn.commit()
        cursor.close()
        conn.close()

    def title_comment_archive(self):
        '''
        Store post titles and their top comments to simulate conversational text
        :return: None (save conversational text to .db)
        '''
        subreddits = ['Politics', 'news', 'Vent', 'askreddit']
        possible_tags = ['[NSFW]', '[nsfw]', '[Serious]', '[serious]', '[SERIOUS]']
        samples = []
        past_urls = [url.replace('\n', '') for url in open('BackgroundTasks/Reddit/url_log.txt', 'r').readlines()]
        current_urls = []
        # iterate over a selection of subreddits with favorable title/comment structure
        for sub in subreddits:
            print('Archiving conversational text from: r/{}'.format(sub))
            for post in self.bot.subreddit(sub).hot(limit=100):
                # don't archive posts that have already been accounted for
                if post.url in past_urls:
                    continue
                else:
                    print(post.title)
                    current_urls.append(post.url)
                # remove stickied posts like mod posts
                if post.stickied:
                    continue
                # clean up title
                title = post.title
                title = re.split('(?<=[.!?]) +', title)[0]
                title = title.split('\n')[0]
                title = ' '.join([word.lower() for word in title.split() if word not in possible_tags])
                title = ''.join([char for char in title if char.isalpha() or char == ' '])
                # reveal all comments
                post.comments.replace_more(limit=None)
                # parse through top comments
                # these don't need to be as clean
                #   - punctuation will make for more natural vocalization
                #   - numbers will have to be corrected for though
                for top_comment in post.comments:
                    if top_comment.author == 'AutoModerator':
                        continue
                    comment = top_comment.body
                    comment = re.split('(?<=[.!?]) +', comment)[0]
                    comment = comment.split('\n')[0]
                    samples.append((title, comment))
        for t, r in samples:
            # this is not clean but too bad
            if r == '[deleted]' or r == '[removed]':
                continue
            h = SHA256.new()
            h.update(t.encode('utf-8'))
            h = ''.join([char for char in h.hexdigest() if char.isalpha()][:25])
            title_len = len(t.split())
            title_pickle_fname = DATA_DIR+'/sentence_matrices/{tl}_{hex}.p'.format(tl=title_len, hex=h)
            if not os.path.isfile(title_pickle_fname):
                # convert the title to a sentence matrix
                sm = convert_sentence_to_matrix(s=t)
                # pickle it
                pickle.dump(sm, open(title_pickle_fname, 'wb'))
            # add the entries to relevant table
            self._store_conversational_text(table_name=h, response_text=r)
        # this is not the best way to do this but i can alter later
        with open('BackgroundTasks/Reddit/url_log.txt', 'w') as f:
            for url in current_urls:
                f.write(url+'\n')
            for url in past_urls[:200*len(subreddits)]:
                f.write(url+'\n')
        print('Completed conversational archiving with {} additions or updates'.format(len(samples)))

    def interests_archive(self):
        '''
        Use this later to do semantic analysis on posts I upvote
        :return: None
        '''
        pass


if __name__ == "__main__":
    rb = RedditBot()
    rb.title_comment_archive()

