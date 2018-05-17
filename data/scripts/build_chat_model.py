'''
Script to generate a model capable of interpreting sentences and documents using Word2Vec algorithm
'''

import gensim
import copy
import os
import pickle
import argparse
import pandas as pd
from MulticoreTSNE import MulticoreTSNE
from tqdm import tqdm
from sklearn.cluster import DBSCAN


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default=None, help='Path to the directory where training text is stored')
    parser.add_argument('--word_model', default=None, help='Path to an existing word2vec model')
    parser.add_argument('--output_path', default='', help='Path to directory where the models will be stored')
    args = parser.parse_args()
    ChatModelConstructor(args)


def transform_sentence(output_path, sentence):
    '''
    Convert a sentence into a cluster id representation.
        - each word is replaced with its cluster ID and joined by '_'
    Intermediary step used by the iterator to transform a sentence into a token that word2vec can work with.
    :return: tokenized_sentence (str)
    '''
    sentence = sentence.split()
    cluster_dict = pickle.load(open(output_path + '/cluster_dict.p', 'rb'))
    clusters = []
    for word in sentence:
        try:
            cluster_id = str(cluster_dict[word])
        except KeyError:
            cluster_id = '-1'
        clusters.append(cluster_id)
    tokenized_sentence = '_'.join(clusters)
    return tokenized_sentence


class MemSafeIterator(object):

    def __init__(self, data_dir, output_dir, mode):
        self.output_dir = output_dir
        self.data_dir = data_dir
        self.mode = mode

    def __iter__(self):
        for fname in os.listdir(self.data_dir):
            print('Iterating over: {}'.format(fname))
            tokenized_sentences = []
            for line in tqdm(open(os.path.join(self.data_dir, fname), 'r').readlines(),
                             total=len(open(os.path.join(self.data_dir, fname), 'r').readlines())):
                if self.mode == 'word':
                    yield line.split()
                elif self.mode == 'sentence':
                    # if the line is just a newline char then yield what has been added and reset
                    if line == '' or line == '\n':
                        yield tokenized_sentences
                        tokenized_sentences = []
                    else:
                        cluster_token = transform_sentence(sentence=line, output_path=self.output_dir)
                        tokenized_sentences.append(cluster_token)
                else:
                    print('Error: unknown iterator mode')
                    exit()


class ChatModelConstructor(object):
    def __init__(self, args):
        self.output_path = args.output_path
        self.data_dir = args.data_dir
        self.word_model = args.word_model
        # check for a provided word model to work from
        if self.word_model is not None:
            # skip the model build and go directly to building sentence model
            self.build_sentence_model()
        else:
            # build everything from scratch
            self.build_word_model()

    def build_word_model(self):
        '''
        Standard word2vec model construction.
        Creates a word model and redefines self.word_model with path.
        :return: None
        '''
        WORKERS = 4
        VEC_SIZE = 150
        MIN_COUNT = 5
        MAX_VOCAB = 250000
        print('Constructing new word2vec model...\n')
        model = gensim.models.word2vec.Word2Vec(sentences=MemSafeIterator(mode='word',
                                                                          data_dir=self.data_dir,
                                                                          output_dir=self.output_path),
                                                workers=WORKERS,
                                                size=VEC_SIZE,
                                                min_count=MIN_COUNT,
                                                max_vocab_size=MAX_VOCAB)
        model.save(self.output_path+'/word.model')
        self.word_model = self.output_path+'/word.model'
        print('\nSaved new word2vec model.\n')
        self.assign_word_clusters()

    def assign_word_clusters(self):
        '''
        Use t-SNE and DBSCAN to cluster the word vectors.
        A pickled dictionary of cluster IDs and their members is created.
        :return: cluster_dict (the unpickled dictionary)
        '''
        model = gensim.models.word2vec.Word2Vec.load(self.word_model)
        word_df = pd.DataFrame(columns=['col_{}'.format(i) for i in range(model.vector_size)] + ['word'])
        print('Creating word clusters...\n')
        print('Vocabulary iteration Progress:')
        for i, word in tqdm(enumerate(model.wv.vocab), total=len(model.wv.vocab), unit='words'):
            word_df.loc[i] = model[word].tolist() + [word]
        only_vecs = copy.deepcopy(word_df)
        only_vecs = only_vecs.drop(['word'], axis=1)
        print('Initiating tSNE and clustering...\n')
        tsne = MulticoreTSNE(n_jobs=4)
        tsne_vecs = tsne.fit_transform(only_vecs)
        dbscan = DBSCAN()
        labels = dbscan.fit_predict(tsne_vecs)
        word_cluster_dict = {}
        for index, row in word_df.iterrows():
            word_cluster_dict[row['word']] = labels[index]
        pickle.dump(word_cluster_dict, open(self.output_path+'/cluster_dict.p', 'wb'))
        self.build_sentence_model()

    def build_sentence_model(self):
        '''
        Use sentences in cluster-token representation to train a word2vec model that can interpret full sentences
        :return: None
        '''
        if 'cluster_dict.p' not in os.listdir(self.output_path):
            print('Error: Unable to find the necessary cluster_dict.p file in specified output_dir.')
            exit()
        WORKERS = 4
        VEC_SIZE = 150
        MIN_COUNT = 2
        MAX_VOCAB = 9999999
        print('Constructing new word2vec based sentence model...\n')
        model = gensim.models.word2vec.Word2Vec(sentences=MemSafeIterator(mode='sentence',
                                                                          data_dir=self.data_dir,
                                                                          output_dir=self.output_path),
                                                workers=WORKERS,
                                                size=VEC_SIZE,
                                                min_count=MIN_COUNT,
                                                max_vocab_size=MAX_VOCAB)
        model.save(self.output_path + '/sentence.model')
        print('Saved new sentence model.\n')


if __name__ == "__main__":
    main()
