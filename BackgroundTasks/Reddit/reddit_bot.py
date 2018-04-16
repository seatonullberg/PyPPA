import sqlite3
import praw
import time
from praw.models import MoreComments
from bs4 import BeautifulSoup
import requests
from api_config import REDDIT_CLIENT_ID, REDDIT_SECRET, REDDIT_USER_AGENT, REDDIT_USERNAME


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

    def collect_upvoted(self):
        # check 100 max but break if a non unique is encountered
        upv = self.user.upvoted(limit=100)
        for u in upv:
            _url = u.url
            # check here to verify unique url
            _title = u.title
            _subreddit = str(u.subreddit)
            # organize comments
            comments = [c.body for c in u.comments.list() if not isinstance(c, MoreComments)]
            # use \n as split char
            _comments = '\n'.join(comments)
            _is_img, _is_post, _is_article = 0, 0, 0
            if _url.endswith('.jpg') or _url.endswith('.png'):
                _is_img = 1
            elif _url.endswith('/'):
                _is_post = 1
            elif _url.endswith('.html'):
                _is_article = 1

            data = {'url': _url, 'subreddit': _subreddit, 'comments': _comments,
                    'title': _title, 'is_img': _is_img, 'is_post': _is_post, 'is_article': _is_article}

            upt = UpvotedPostsTable()
            if upt.is_unique(url=data['url']):
                upt.submit_entry(data)
                print('Adding Reddit URL: ', data['url'])
            else:
                break


class UpvotedPostsTable(object):

    def __init__(self):
        # use reddit.db as file across reddit stuff
        # this method of path selection should change
        try:
            self.conn = sqlite3.connect('BackgroundTasks/Reddit/reddit.db')
        except sqlite3.OperationalError:
            self.conn = sqlite3.connect('reddit.db')
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
        comments = [c[0].split('\n') for c in comments]
        formatted_comments = []
        for c in comments:
            for cc in c:
                formatted_comments.append(cc)

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
                    articles.append(p)

        # each data type in its own list
        return titles, formatted_comments, articles
