import praw
import re
import os
from base_background_task import BaseBackgroundTask


class RedditTasks(BaseBackgroundTask):

    def __init__(self):
        CLIENT_ID = self.config_obj.environment_variables['RedditTasks']['CLIENT_ID']
        SECRET = self.config_obj.environment_variables['RedditTasks']['SECRET']
        USER_AGENT = self.config_obj.environment_variables['RedditTasks']['USER_AGENT']
        USERNAME = self.config_obj.environment_variables['RedditTasks']['USERNAME']

        self.BOT = praw.Reddit(client_id=CLIENT_ID,
                               client_secret=SECRET,
                               user_agent=USER_AGENT)
        self.USER = self.BOT.redditor(USERNAME)

        self._name = 'reddit_tasks'
        # archive text hourly
        self.delays = [(self.archive_text, 3600)]
        super().__init__(name=self._name,
                         delays=self.delays)

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
            comments_path = [DATA_DIR, 'text', 'Reddit', 'comments.txt']
            with open(os.path.join('', *comments_path), 'a') as f:
                for comment in post.comments.list():
                    if comment.author == 'AutoModerator':
                        continue
                    elif comment.body in null_comments:
                        continue
                    comment_list = self.clean_comment(comment.body)  # returns list
                    for c in comment_list:
                        f.write(c + '\n')
                # after all comments are written use a blank line to indicate separation of posts
                f.write('\n')
        print('Reddit text archiving complete.')

        # TODO...after testing the sentence vectors:
        # conversationally structured text
        # - hash the sentence then use as a table name and .p filename
        # - common responses to this sentence are stored in the table
        # - the sentence vector is stored in the .p file
        '''
            # iterate through comments, rebuilding the hierarchical structure only to second level
            post.comments.replace_more(limit=None)
            parent_children_pairing = [None, []]  # contains the head comment and a list of responses
            for c in post.comments:
                parent_children_pairing[0] = c.body
                for reply in c.replies:
                    parent_children_pairing[1].append(reply.body)
            all_post_comments.append(parent_children_pairing)

        # clean the comments
        head_comments = [apc[0] for apc in all_post_comments]
        head_comments = clean_comments(head_comments)
        for apc, head in zip(all_post_comments, head_comments):
            apc[0] = head
        for apc in all_post_comments:
            apc[1] = clean_comments(apc[1])
        '''

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


