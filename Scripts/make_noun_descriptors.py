'''
This script is in limbo until I decide how to proceed with the chat model
- contains a few useful snippets I might need later but not integral
'''
from private_config import DATA_DIR
import spacy
import sqlite3
import tensorflow as tf
import string


def make_noun_descriptors():
    '''
    Collect descriptors of nouns based on verbs, adjectives, and other nouns
    :param texts: list of sentences to be analyzed
    :return: None, fills database with descriptors
    '''
    # load in the raw_texts first
    load_conn = sqlite3.connect(DATA_DIR+'/raw_text.db')
    load_cursor = load_conn.cursor()
    load_cursor.execute("SELECT content FROM raw_text")
    raw_text = load_cursor.fetchall()
    raw_text = [r[0] for r in raw_text]
    load_conn.close()
    # load the spacy model and connect to db
    nlp = spacy.load('en_core_web_lg')
    conn = sqlite3.connect(DATA_DIR+"/noun_descriptors.db")
    cursor = conn.cursor()
    # iterate over every text entry in the raw_text.db
    for i, t in enumerate(raw_text):
        progress = (i/len(raw_text))*100
        progress = round(progress, 2)
        print("Percent Complete: {}%\r".format(str(progress)))
        # avoid oversized inputs
        try:
            doc = nlp(t)
        except ValueError:
            print('Text was too large to process; skipping')
            continue

        # verify that tokens are valid words
        revised_doc = [token for token in doc]
        for token in doc:
            for char in token.text:
                if char not in string.ascii_letters:
                    revised_doc.remove(token)
                    break
        # define all noun entries before moving through whole sentence
        nouns = {}
        for token in revised_doc:
            if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                nouns[token.text] = []
                # catch verbs in this loop as well
                if token.dep_ == 'nsubj' or token.dep_ == 'dobj':
                    nouns[token.text].append((token.head.text, "VERB"))
        # reiterate to find relevant adjectives
        for token in revised_doc:
            if token.pos_ == "ADJ" and token.dep_ == 'amod':
                try:
                    nouns[token.head.text].append((token.text, "ADJ"))
                except KeyError:
                    print('{x} was not stored as a noun, but is described by {y}.'.format(x=token.head.text,
                                                                                          y=token.text))
                    continue
        # add the descriptors to the db
        for n in nouns:
            try:
                cursor.execute("CREATE TABLE IF NOT EXISTS {} (word text, pos text)".format(str(n)))
                conn.commit()
            except sqlite3.OperationalError:
                print("{} is a bad table name".format(str(n)))
                continue
            except sqlite3.DatabaseError:
                print('Database error when creating table {}'.format(str(n)))
                continue
            for descriptors in nouns[n]:
                cursor.execute("INSERT INTO {} VALUES (?,?)".format(n), [descriptors[0], descriptors[1]])
                conn.commit()
            for sub_n in nouns:
                if sub_n != n:
                    cursor.execute("INSERT INTO {} VALUES (?,?)".format(n), [sub_n, "NOUN"])
                    conn.commit()
    conn.close()
    print('Noun descriptors complete')


if __name__ == "__main__":
    '''
    with tf.device('/device:GPU:0'):
        make_noun_descriptors()
    '''
    '''
    conn = sqlite3.connect('raw_text.db')
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM raw_text WHERE type=?", ['reddit_comment'])
    res = cursor.fetchall()
    res = [r[0] for r in res]
    print(res)

    '''

    '''
    conn = sqlite3.connect('noun_descriptors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    res = cursor.fetchall()
    res = [r[0] for r in res]
    print(res)

    '''

    connect = sqlite3.connect('noun_descriptors.db')
    cur = connect.cursor()
    cur.execute("SELECT word FROM money WHERE pos=?", ["ADJ"])
    res = cur.fetchall()
    res = [r[0] for r in res]
    print(set(res))
