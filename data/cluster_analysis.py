import time
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.manifold.t_sne import TSNE
import pandas as pd
import matplotlib.pyplot as plt


def normalize_data(arr):
    scaler = StandardScaler()
    return scaler.fit_transform(arr)


def apply_pca(arr):
    pca = PCA()
    return pca.fit_transform(arr)


def apply_tsne(arr):
    tsne = TSNE(n_components=3)
    return tsne.fit_transform(arr)


def label_clusters(arr):
    dbscan = DBSCAN(min_samples=10, eps=.7)
    return dbscan.fit_predict(arr)


def plot_2d(df):
    title = 'Clusters of Word Vectors'
    _clusterids = set(df['cluster_id'])
    _clusterids.remove(-1)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    for clusterid in _clusterids:
        x = df.loc[df['cluster_id'] == clusterid]['col_0']
        y = df.loc[df['cluster_id'] == clusterid]['col_1']
        ax.scatter(x, y, s=1)
    plt.title(s=title)
    plt.savefig('word_cluster_tsne_fig_2d')


def plot_3d(df):
    title = 'Clusters of Word Vectors'
    _clusterids = set(df['cluster_id'])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for clusterid in _clusterids:
        x = df.loc[df['cluster_id'] == clusterid]['col_0']
        y = df.loc[df['cluster_id'] == clusterid]['col_1']
        z = df.loc[df['cluster_id'] == clusterid]['col_2']
        ax.scatter(x, y, z, s=1)
    plt.title(s=title)
    plt.show()
    plt.savefig('word_cluster_tsne_fig_3d')


if __name__ == "__main__":
    print('Started Loading: {}'.format(time.ctime()))
    data = np.load('wiki.model.wv.vectors.npy')
    data = data[:400000,:]
    print('Finished Loading: {}'.format(time.ctime()))
    norm_data = normalize_data(data)
    print('Finished Normalizing: {}'.format(time.ctime()))
    pca_data = apply_pca(norm_data)
    print('Finished PCA: {}'.format(time.ctime()))
    tsne_data = apply_tsne(pca_data)
    print('Finished t-SNE: {}'.format(time.ctime()))
    labels = label_clusters(tsne_data)
    print("Cluster IDs: {}".format(set(labels)))
    clusters_df = pd.DataFrame(data=tsne_data, columns=['col_{}'.format(i) for i in range(tsne_data.shape[1])])
    clusters_df['cluster_id'] = labels
    plot_2d(clusters_df)
    plot_3d(clusters_df)
    print('Saved Figure: {}'.format(time.ctime()))

    # save the df!
    clusters_df.to_csv('dbscan_clustered_words_in_tsne_space.csv')
