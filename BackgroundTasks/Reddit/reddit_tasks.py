from tqdm import tqdm
import sqlite3
import praw
import time
from praw.models import MoreComments
import re
import os
import pickle
import multiprocessing
from Crypto.Hash import SHA256
from private_config import REDDIT_USERNAME, REDDIT_USER_AGENT, REDDIT_SECRET, REDDIT_CLIENT_ID, DATA_DIR

BOT = praw.Reddit(client_id=REDDIT_CLIENT_ID,
                  client_secret=REDDIT_SECRET,
                  user_agent=REDDIT_USER_AGENT)
USER = BOT.redditor(REDDIT_USERNAME)


def startup():
    # run all functions that are not private or startup
    funcs = [archive_text]
    for func in funcs:
        func()
    # kill the process once complete to free space
    for proc in multiprocessing.active_children():
        if proc.name == 'reddit_tasks':
            proc.terminate()
            proc.join()


def clean_comment(comment):
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


def archive_text():
    '''
    Collect Reddit comments for raw text data and conversational text data
    - conversational not currently implemented
    :return: None (writes data to file)
    '''
    past_urls_path = [DATA_DIR, 'background_logs', 'Reddit', 'text_url_log.txt']
    past_urls = [url.replace('\n', '') for url in open(os.path.join('', *past_urls_path), 'r').readlines()]
    # iterate over the 100 top posts
    for post in BOT.subreddit('popular').hot(limit=100):
        all_post_comments = []
        # ignore previously archived posts
        if post.url in past_urls:
            continue
        # ignore sticky posts
        elif post.stickied:
            continue
        else:
            print('Archiving text from: {}'.format(post.title))
            # add this new url to old url list for future reference
            with open(os.path.join('', *past_urls_path), 'a') as f:
                f .write(post.url+'\n')

        # reveal all comments in post
        post.comments.replace_more(limit=None)
        null_comments = ['[Removed]', '[removed]', '[Deleted]', '[deleted]']
        # write unstructured clean text to file
        comments_path = [DATA_DIR, 'text', 'Reddit', 'comments.txt']
        with open(os.path.join('', *comments_path), 'a') as f:
            for comment in tqdm(post.comments.list(), total=len(post.comments.list()), unit=' comments'):
                if comment.author == 'AutoModerator':
                    continue
                elif comment.body in null_comments:
                    continue
                comment_list = clean_comment(comment.body)   # returns list
                for c in comment_list:
                    f.write(c+'\n')
            # after all comments are written use a blank line to indicate separation of posts
            f.write('\n')
    print('Reddit text archiving complete.')

    # TODO...after testing the sentence vectors:
    # conversationally structured next
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


# Use later with upvoted posts
def archive_interests():
    pass
