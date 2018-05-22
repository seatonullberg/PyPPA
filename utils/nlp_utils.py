import gensim
import numpy as np
from private_config import DATA_DIR
import scipy.spatial as sp


def convert_sentence_to_matrix(s, model_fname=DATA_DIR+'/models/wiki.model', max_len=25):
    '''
    :param s: singular sentence of input to convert to a matrix
    :param model_fname: name of the model used to pull word vectors from
    :param max_len: max number of words that the sentence matrix will account for
    :return: sentence_matrix (numpy.ndarray) a concatenation of word vectors used to represent meaning in a sentence
    '''
    model = gensim.models.word2vec.Word2Vec.load(model_fname)
    model_columns = model.layer1_size

    if len(s) > max_len:
        s = s[:max_len]
    sentence_matrix = np.zeros(shape=(max_len, model_columns))
    for i, word in enumerate(s):
        try:
            word_vec = model[word]
        except KeyError:
            # if the word is not in vocab exclude it from the representation
            # gets represented as a row of zeroes
            continue
        sentence_matrix[i, :] = word_vec

    return sentence_matrix
