import spacy
import sqlite3
from BackgroundTasks.Reddit.reddit_bot import UpvotedPostsTable
"""
Run this after a substantial amount of data is in reddit.db
to collect noun descriptors
"""


def process_reddit_content(texts):
    '''
    Collect descriptors of nouns based on verbs, adjectives, and other nouns
    :param texts: list of sentences to be analyzed
    :return: None, fills database with descriptors
    '''
    nlp = spacy.load('en_core_web_lg')
    conn = sqlite3.connect("noun_descriptors.db")
    cursor = conn.cursor()
    for i, t in enumerate(texts):
        progress = (i/len(texts))*100
        progress = round(progress, 2)
        print("Percent Complete: {}%".format(str(progress)))
        doc = nlp(t)
        nouns = {}
        # define all noun entries before moving through whole sentence
        for token in doc:
            if not token.text.isalpha():
                continue
            if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                nouns[token.text] = []
                # catch verbs in this loop as well
                if token.dep_ == 'nsubj' or token.dep_ == 'dobj':
                    nouns[token.text].append((token.head.text, "VERB"))
        # reiterate to find relevant adjectives
        for token in doc:
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
            except sqlite3.OperationalError:
                print("{} is a bad table name".format(str(n)))
                continue
            for descriptors in nouns[n]:
                cursor.execute("INSERT INTO {} VALUES (?,?)".format(n), [descriptors[0], descriptors[1]])
                conn.commit()
            for sub_n in nouns:
                if sub_n != n:
                    cursor.execute("INSERT INTO {} VALUES (?,?)".format(n), [sub_n, "NOUN"])
                    conn.commit()
    conn.close()


if __name__ == "__main__":
    upt = UpvotedPostsTable()
    titles, comments, articles = upt.export()
    for text in [titles, comments, articles]:
        process_reddit_content(text)

    '''
    connect = sqlite3.connect('noun_descriptors.db')
    cur = connect.cursor()
    cur.execute("SELECT word FROM Trump WHERE pos=?", ["VERB"])
    res = cur.fetchall()
    res = [r[0] for r in res]
    print(set(res))
    '''