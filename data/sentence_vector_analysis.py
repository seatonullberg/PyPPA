import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from MulticoreTSNE import MulticoreTSNE as tSNE


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


if __name__ == "__main__":
    pick = pickle.load(open('pickled_sent_vecs', 'rb'))
    reduced_info = [p[1] for p in pick]
    x = [r[0] for r in reduced_info]
    y = [r[1] for r in reduced_info]
    arr = np.vstack((x,y)).T
    arr = normalize_data(arr)
    arr = apply_tsne(arr)
    df = pd.DataFrame(data=arr, columns=['x', 'y'])
    df['cluster_id'] = make_clusters(df)
    plot_2d(df)
