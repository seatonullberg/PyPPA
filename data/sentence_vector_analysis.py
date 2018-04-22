import numpy as np
import gensim
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from MulticoreTSNE import MulticoreTSNE as tSNE

'''
TODO:
- cannot get good results with bad dataset
-- use the wiki data which the word vectors are trained on for best results
--- make a memory efficient iterator to make vectors from wiki data
'''


def normalize_data(data):
    scaler = StandardScaler()
    return scaler.fit_transform(data)


def apply_tsne(data):
    tsne = tSNE(n_jobs=4, perplexity=10)
    return tsne.fit_transform(data)


def make_clusters(data):
    dbscan = DBSCAN(min_samples=10)
    labels = dbscan.fit_predict(data)
    return labels


def plot_2d(data):
    title = 'Clusters of Sentence Vectors'
    _clusterids = set(df['cluster_id'])
    _clusterids.remove(-1)
    print(_clusterids)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for clusterid in _clusterids:
        x = data.loc[data['cluster_id'] == clusterid]['x']
        y = data.loc[data['cluster_id'] == clusterid]['y']
        ax.scatter(x, y, s=1)
    plt.title(s=title)
    plt.show()


def intracluster_validation(cluster_id, data, sentence_arrs):
    model = gensim.models.word2vec.Word2Vec.load('wiki.model')
    reduced_arrs = data.loc[data['cluster_id'] == cluster_id]
    indices = reduced_arrs.index.tolist()
    for id in indices:
        sentence_arr = sentence_arrs[id]
        sentence = []
        for word_vecs in sentence_arr:
            word = model.similar_by_vector(word_vecs, topn=1, restrict_vocab=None)
            if word[0][1] > 0.95:
                sentence.append(word[0][0])
            else:
                sentence.append('_NULL_')
        print(' '.join(sentence))


if __name__ == "__main__":
    pick = pickle.load(open('sentence_vecs.p', 'rb'))
    x = []
    y = []
    full_arr = []
    for tup in pick:
        x.append(tup[1][0])
        y.append(tup[1][1])
        full_arr.append(tup[0])
    arr = np.vstack((x, y)).T
    arr = normalize_data(arr)
    arr = apply_tsne(arr)
    df = pd.DataFrame(data=arr, columns=['x', 'y'])
    df['cluster_id'] = make_clusters(df)
    intracluster_validation(50, df, full_arr)
    plot_2d(df)
