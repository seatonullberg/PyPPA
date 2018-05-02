import gensim
import time
import os
from private_config import DATA_DIR
import pandas as pd
import copy
from MulticoreTSNE import MulticoreTSNE
from sklearn.cluster import DBSCAN
import pickle
from tqdm import tqdm


class MemSafeCorpusIterator(object):

    def __init__(self, dirname):
        self.dirname = dirname

    def __iter__(self):
        for fname in os.listdir(self.dirname):
            print('Iterating over: {}'.format(fname))
            for line in open(os.path.join(self.dirname, fname)):
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


def make_model(corpus_path, vec_size, count_min, vocab_size_max, model_name):
    print('Start Time: {}'.format(time.ctime()))
    model = gensim.models.word2vec.Word2Vec(sentences=MemSafeCorpusIterator(corpus_path),
                                            workers=4,
                                            size=vec_size,
                                            min_count=count_min,
                                            max_vocab_size=vocab_size_max)
    print('Trained at: {}'.format(time.ctime()))
    print(model.wv.most_similar('food'))
    model.save('{}.model'.format(model_name))
    print({'Saved at: {}'.format(time.ctime())})


def assign_clusters(model_fname):
    model = gensim.models.word2vec.Word2Vec.load(model_fname)
    word_df = pd.DataFrame(columns=['col_{}'.format(i) for i in range(model.vector_size)]+['word'])
    for i, word in tqdm(enumerate(model.wv.vocab)):
        word_df.loc[i] = model[word].tolist()+[word]
    print('Completed iteration: {}'.format(time.ctime()))
    only_vecs = copy.deepcopy(word_df)
    only_vecs = only_vecs.drop(['word'], axis=1)
    tsne = MulticoreTSNE(n_jobs=4)
    print('Running tSNE: {}'.format(time.ctime()))
    tsne_vecs = tsne.fit_transform(only_vecs)
    dbscan = DBSCAN()
    print('Clustering with DBSCAN: {}'.format(time.ctime()))
    labels = dbscan.fit_predict(tsne_vecs)
    # word_df['cluster_id'] = pd.Series(labels, index=word_df.index)
    print('Filling word_cluster_dict: {}'.format(time.ctime()))
    word_cluster_dict = {}
    for index, row in word_df.iterrows():
        word_cluster_dict[row['word']] = labels[index]
    pickle.dump(word_cluster_dict, open('word_cluster_dict.p', 'wb'))
    print('Done: {}'.format(time.ctime()))


if __name__ == "__main__":
    assign_clusters(DATA_DIR+'/models/wiki.model')
