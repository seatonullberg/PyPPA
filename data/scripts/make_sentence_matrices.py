import gensim
import numpy as np
import os
import pickle
from private_config import DATA_DIR
import time
import scipy.spatial as sp


def sanity_check(s1, s2, model_fname):
    m1 = np.zeros((25, 100))
    m2 = np.zeros((25, 100))
    model = gensim.models.word2vec.Word2Vec.load(model_fname)
    for i, word in enumerate(s1.split()):
        try:
            wv = model[word]
        except KeyError:
            continue
        m1[i, :] = wv

    for i, word in enumerate(s2.split()):
        try:
            wv = model[word]
        except KeyError:
            continue
        m2[i, :] = wv

    distance = sp.distance.cdist(m1, m2, 'euclidean')
    distance = np.nan_to_num(distance, copy=False)
    cum_dist = 0
    for i, dm in enumerate(distance):
        cum_dist += dm[i]
    print(cum_dist)



def mem_safe_sentences(dirname):
    for fname in os.listdir(dirname):
        print('Iterating over: {}'.format(fname))
        for line in set(open(os.path.join(dirname, fname))):
            # at least 5 words to a line
            if len(line.split()) >= 5:
                formatted_line = []
                for word in line.split():
                    # make all inputs lowercase
                    word = word.lower()
                    for char in word:
                        # ensure word has no punctuation attached
                        if not char.isalpha():
                            word = word.replace(char, '')
                    formatted_line.append(word)
                yield formatted_line


class MakeSentenceMatrices(object):

    def __init__(self, model_fname, generator):
        self.max_len = 25   # max number of words in a sentence
        self.model = gensim.models.word2vec.Word2Vec.load(model_fname)
        self.model_rows = len(self.model.wv.vocab)
        self.model_columns = self.model.layer1_size
        self.generator = generator
        self._make_matrices()

    def _make_matrices(self):
        while True:
            try:
                s = next(self.generator)
            except StopIteration:
                print('completed_iteration: {}'.format(time.ctime()))
                break
            if len(s) > self.max_len:
                s = s[:self.max_len]
            sentence_array = np.zeros(shape=(self.max_len, self.model_columns))
            for i, word in enumerate(s):
                try:
                    word_vec = self.model[word]
                except KeyError:
                    # if the word is not in vocab exclude it from the representation
                    # gets represented as a row of zeroes
                    continue
                sentence_array[i, :] = word_vec
            self._save_to_disk((s, sentence_array))

    def _save_to_disk(self, data):
        sm_dir = DATA_DIR+'/sentence_matrices'
        sm_files = os.listdir(sm_dir)
        index = len(sm_files)
        pickle.dump(data, open(sm_dir+"/sm_{}.p".format(index), 'wb'))


if __name__ == "__main__":
    #sm = MakeSentenceMatrices(model_fname='wiki.model', generator=mem_safe_sentences('text/reddit'))
    sent1 = 'hey how are you feeling today'
    sent2 = 'hey how are you doing today'
    sanity_check(s1=sent1, s2=sent2, model_fname='wiki.model')
