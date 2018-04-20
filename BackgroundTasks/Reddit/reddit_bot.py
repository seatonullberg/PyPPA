import sqlite3
import praw
import time
from praw.models import MoreComments
from bs4 import BeautifulSoup
import requests
import re
from api_config import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT, REDDIT_USERNAME, DATA_DIR


class RedditBot(object):

    def __init__(self):
        self.FREQUENCY = 43200   # repeat every 12 hours
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

    def archive_(self):
        # check 100 posts max but break if a non unique is encountered
        upt = UpvotedPostsTable()
        upv = self.user.upvoted(limit=100)
        with open('data/text/reddit/comments.txt', 'a') as f:
            for u in upv:
                _url = u.url
                _title = u.title
                _subreddit = str(u.subreddit)
                # organize comments
                _comments = []
                comments = [re.split('(?<=[.!?]) +', c.body) for c in u.comments if not isinstance(c, MoreComments)]
                for split in comments:
                    for line in split:
                        # test to make sure normal chars are used
                        try:
                            test = line.encode('ascii')
                        except UnicodeEncodeError:
                            continue
                        else:
                            _comments.append(line)
                _comments = '\n'.join(_comments)
                _is_img, _is_post, _is_article = 0, 0, 0
                if _url.endswith('.jpg') or _url.endswith('.png'):
                    _is_img = 1
                elif "www.reddit.com" in _url:
                    _is_post = 1
                else:
                    _is_article = 1
                data = {'url': _url, 'subreddit': _subreddit, 'comments': _comments,
                        'title': _title, 'is_img': _is_img, 'is_post': _is_post, 'is_article': _is_article}
                # push all data to the db
                # push comments to ~/data
                if upt.is_unique(url=data['url']):
                    print('Adding: ', data['url'])
                    upt.submit_entry(data)
                    f.write(_comments)
                else:
                    break
            f.close()


class UpvotedPostsTable(object):

    def __init__(self):
        self.conn = sqlite3.connect('BackgroundTasks/Reddit/reddit.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS upvoted_posts ({})".format(
            "url text NOT NULL, subreddit text, comments text, title text, is_img integer, is_post integer, is_article integer"
        ))

    def __del__(self):
        try:
            self.conn.close()
        except AttributeError:
            print("'UpvotedPostsTable' object has no attribute 'conn'")
            print("Closing anyways")

    def is_unique(self, url):
        self.cursor.execute("SELECT * FROM upvoted_posts WHERE url=?", [url])
        if len(self.cursor.fetchall()) > 0:
            return False
        else:
            return True

    def submit_entry(self, data):
        self.cursor.execute("INSERT INTO upvoted_posts ({}) VALUES (?,?,?,?,?,?,?)".format(
            "url, subreddit, comments, title, is_img, is_post, is_article"
        ), [data['url'], data['subreddit'], data['comments'], data['title'], data['is_img'], data['is_post'], data['is_article']])
        self.conn.commit()

    def export(self):
        # load articles, comments, and titles into useful format
        # prep titles first
        self.cursor.execute("SELECT title FROM upvoted_posts")
        titles = self.cursor.fetchall()
        titles = [t[0] for t in titles]

        # prep comments next
        self.cursor.execute("SELECT comments FROM upvoted_posts")
        comments = self.cursor.fetchall()
        formatted_comments = [c[0].split('\n') for c in comments]
        # prep articles last
        self.cursor.execute("SELECT url FROM upvoted_posts WHERE is_article=?", [1])
        article_urls = self.cursor.fetchall()
        article_urls = [a[0] for a in article_urls]
        articles = []
        for url in article_urls:
            try:
                r = requests.get(url).content
            except:
                print('Could not open {} to extract article sentences.'.format(url))
            else:
                soup = BeautifulSoup(r, "html5lib")
                paragraphs = soup.find_all('p')
                paragraphs = [p.text for p in paragraphs]
                for p in paragraphs:
                    for sentences in p.split('.'):
                        assert type(sentences) == str
                        articles.append(sentences+'.')

        # each data type in its own list
        return titles, formatted_comments, articles
