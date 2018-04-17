import sqlite3
import praw
import time
from praw.models import MoreComments
from bs4 import BeautifulSoup
import requests
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

    def collect_upvoted(self):
        # check 100 max but break if a non unique is encountered
        upt = UpvotedPostsTable()
        upv = self.user.upvoted(limit=1)
        for u in upv:
            _url = u.url
            # check here to verify unique url
            _title = u.title
            _subreddit = str(u.subreddit)
            # organize comments
            comments = [c.body for c in u.comments if not isinstance(c, MoreComments)]
            for c in comments:
                assert type(c) == str
            _comments = str('\n'.join(comments))
            _is_img, _is_post, _is_article = 0, 0, 0
            if _url.endswith('.jpg') or _url.endswith('.png'):
                _is_img = 1
            elif "www.reddit.com" in _url:
                _is_post = 1
            else:
                _is_article = 1
            assert type(_title) == str
            data = {'url': _url, 'subreddit': _subreddit, 'comments': _comments,
                    'title': _title, 'is_img': _is_img, 'is_post': _is_post, 'is_article': _is_article}

            if upt.is_unique(url=data['url']):
                upt.submit_entry(data)
                print('Adding: ', data['url'])
            else:
                break
        upt.export(out='txt')


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

    def export(self, out=None):
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
                    for sentences in p.split('.'):
                        assert type(sentences) == str
                        articles.append(sentences+'.')

        if out == 'db':
            export_db = sqlite3.connect(DATA_DIR+'/raw_text.db')
            export_cursor = export_db.cursor()
            export_cursor.execute("CREATE TABLE IF NOT EXISTS raw_text (content text, type text)")
            export_db.commit()
            for content, content_type in zip([titles, formatted_comments, articles],
                                             ['reddit_title', 'reddit_comment', 'reddit_article']):
                print('Exporting: '+content_type)
                for text in content:
                    try:
                        export_cursor.execute("INSERT INTO raw_text VALUES (?,?)", [text, content_type])
                        export_db.commit()
                    except sqlite3.OperationalError:
                        print("Unable to add: {}".format(text))
                        continue
            print('Export Complete')
        elif out == 'txt':
            print('Exporting: reddit_comment')
            with open(DATA_DIR + '/raw_text.txt', 'a') as f:
                for c in formatted_comments:
                    c = c.replace('.', '.\n')
                    c = c.replace('?', '?\n')
                    c = c.replace('!', '!\n')
                    for line in c.split('\n'):
                        try:
                            line.encode('ascii')
                        except UnicodeEncodeError:
                            print('Bad str: '+line)
                            c = '\n'
                    # this needs to be tweaked to clean up the data input
                    f.write(c+'\n')
                f.close()
            print('Export Complete')
        else:
            # each data type in its own list
            return titles, formatted_comments, articles
