import gensim
import numpy as np
from sklearn.decomposition import PCA
import pickle
import os


class MemSafeCorpusIterator(object):

    def __init__(self, dirname):
        self.dirname = dirname

    def __iter__(self):
        for fname in os.listdir(self.dirname):
            print('Iterating over: {}'.format(fname))
            for line in open(os.path.join(self.dirname, fname)):
                if len(line.split()) > 2:
                    yield line.split()


class MakeSentenceVectors(object):

    def __init__(self, model_fname, corpus):
        self.model = gensim.models.word2vec.Word2Vec.load(model_fname)
        self.model_rows, self.model_columns = np.load(model_fname+'.wv.vectors.npy').shape
        self.output = []
        self.corpus = corpus
        self._transform_sentence()

    def _transform_sentence(self):
        # iterate over all entries in corpus
        for sentence in self.corpus:
            # initialize an array to hold word vectors
            sentence_array = np.ndarray(self.model_columns,)
            for word in sentence:
                try:
                    word_vec = self.model[word]
                except KeyError:
                    # if the word is not in vocab represent it as all zeroes
                    word_vec = np.zeros(self.model_columns,)
                # stack the word vectors together
                sentence_array = np.vstack((sentence_array, word_vec))
            # remove the initial column that was used for convenience
            sentence_array = sentence_array[1:]
            # shape is now (n_words, n_dims)
            # use pca to order by variance
            reduced_array = self._pca_reduce(sentence_array)
            reduced_array = reduced_array[:2]
            # transpose the reduced array and repeat pca to further reduce
            # THIS REQUIRES THE SENTENCES TO BE AT LEAST 2 WORDS LONG; VERIFY THAT PRIOR TO INPUT
            reduced_array = reduced_array.T
            reduced_array = self._pca_reduce(reduced_array)
            reduced_array = reduced_array[:2]
            # take only the first row because the second is just the negated first
            reduced_array = reduced_array[0]
            # shape is now (2,) and will be for all valid inputs
            # add a tuple to the collection for further processing
            self.output.append((sentence_array, reduced_array))

    def _pca_reduce(self, arr):
        pca = PCA()
        pca_arr = pca.fit_transform(arr)
        return pca_arr

    def pickle_output(self, fname):
        pickle.dump(self.output, open(fname, 'wb'))


if __name__ == "__main__":
    c = [['the', 'cow', 'jumped', 'over', 'the', 'moon']]
    sv = MakeSentenceVectors(model_fname='wiki.model', corpus=MemSafeCorpusIterator('text/reddit'))
    sv.pickle_output('pickled_sent_vecs')
