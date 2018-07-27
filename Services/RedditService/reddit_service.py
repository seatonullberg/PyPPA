from base_service import BaseService
import praw
import os
import re


class RedditService(BaseService):

    def __init__(self):
        self.name = 'RedditService'
        self.input_filename = 'reddit_service.in'
        self.output_filename = 'reddit_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

        CLIENT_ID = self.config_obj.environment_variables['RedditTasks']['CLIENT_ID']
        SECRET = self.config_obj.environment_variables['RedditTasks']['SECRET']
        USER_AGENT = self.config_obj.environment_variables['RedditTasks']['USER_AGENT']
        USERNAME = self.config_obj.environment_variables['RedditTasks']['USERNAME']

        self.BOT = praw.Reddit(client_id=CLIENT_ID,
                               client_secret=SECRET,
                               user_agent=USER_AGENT)
        self.USER = self.BOT.redditor(USERNAME)

    def default(self):
        # every hour run text archival
        if self.clock.since_output > 3600:
            self.archive_text()

    def archive_text(self):
        '''
                Collect Reddit comments for raw text data and conversational text data
                - conversational not currently implemented
                :return: None (writes data to file)
                '''
        DATA_DIR = self.config_obj.environment_variables['Base']['DATA_DIR']
        past_urls_path = [DATA_DIR, 'background_logs', 'Reddit', 'text_url_log.txt']
        past_urls = [url.replace('\n', '') for url in open(os.path.join('', *past_urls_path), 'r').readlines()]
        # iterate over the 100 top posts
        for post in self.BOT.subreddit('popular').hot(limit=100):
            # ignore previously archived posts
            if post.url in past_urls:
                continue
            # ignore sticky posts
            elif post.stickied:
                continue
            else:
                print('Archiving {c} comments from: {t}\n'.format(
                    t=post.title,
                    c=len(post.comments.list()),
                )
                )
                # add this new url to old url list for future reference
                with open(os.path.join('', *past_urls_path), 'a') as f:
                    f.write(post.url + '\n')

            # reveal all comments in post
            post.comments.replace_more(limit=None)
            null_comments = ['[Removed]', '[removed]', '[Deleted]', '[deleted]']
            # write unstructured clean text to file
            for comment in post.comments.list():
                if comment.author == 'AutoModerator':
                    continue
                elif comment.body in null_comments:
                    continue
                comment_list = self.clean_comment(comment.body)  # returns list
                for c in comment_list:
                    c += '\n'
                    self.output(c)
        print('Reddit text archiving complete.')

    def clean_comment(self, comment):
        '''
        Clean a single Reddit comment for input as raw text data
        :param comment: str() body of a Reddit comment
        :return: clean_comment_list list() the comment split on punctuation and devoid of distractions
        '''
        # make all lowercase
        comment = comment.lower()
        # remove new lines
        comment = comment.replace('\n', ' ')
        # remove content between parentheses
        comment = re.sub(r'\([^()]*\)', '', comment)
        # remove non ascii
        comment = re.sub(r'[^\x00-\x7f]', '', comment)
        # remove links
        comment = ' '.join(c for c in comment.split() if not c.startswith('http'))
        # remove subreddit references
        comment = ' '.join([c for c in comment.split() if not c.startswith('r/') and not c.startswith('/r/')])
        # ensure single spaced
        comment = ' '.join(c for c in comment.split() if c != ' ')
        # split on punctuation
        comment_list = re.split('(?<=[.!?]) +', comment)
        # remove residual non alpha chars
        clean_comment_list = []
        for comm in comment_list:
            comm = ''.join([c for c in comm if c.isalpha() or c == ' '])
            if comm != '':
                clean_comment_list.append(comm)
        return clean_comment_list
