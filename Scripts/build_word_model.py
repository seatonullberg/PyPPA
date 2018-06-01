# word2vec model generation

import gensim
import os
from tqdm import tqdm
import argparse
import numpy as np


class MemSafeIterator(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def __iter__(self):
        for fname in os.listdir(self.data_dir):
            print('Iterating over: {}'.format(fname))
            pbar = tqdm(total=len(open(os.path.join(self.data_dir, fname), 'r').readlines()), unit=' lines')
            for line in open(os.path.join(self.data_dir, fname), 'r').readlines():
                # split on spaces to get individual words
                yield line.split()
                pbar.update(1)
            pbar.close()
        print('\n')


def make_model(args):
    data_dir = args.data_dir
    _workers = 8
    _vec_size = 300
    _min_count = 5
    _max_vocab = 500000
    _iter = 4
    print('Constructing word model...\nEach input file will be iterated over {} times.\n'.format(_iter+1))
    model = gensim.models.word2vec.Word2Vec(sentences=MemSafeIterator(data_dir=data_dir),
                                            workers=_workers,
                                            size=_vec_size,
                                            min_count=_min_count,
                                            max_vocab_size=_max_vocab,
                                            iter=_iter)
    model.save(os.path.join(args.output_dir, 'word.model'))
    print('Saved new model.')
    print('Vocabulary Size: {}\n'.format(len(model.wv.vocab)))


def test_model(args):
    model = gensim.models.Word2Vec.load(os.path.join(args.output_dir, 'word.model'))
    # select a few words to explore general performance of model
    test_words = model.wv.index2word[100:125]
    for word in test_words:
        print(word)
        print(model.wv.most_similar(word))
        print('\n')


def preprocess_data(args):
    for fname in os.listdir(args.data_dir):
        print('Preprocessing: {}'.format(fname))
        file = os.path.join(args.data_dir, fname)
        # any files that are significantly larger than 1 gig get partitioned
        if os.stat(file).st_size > 1.2e9:
            # find number of files to split to
            nfiles = int(os.stat(file).st_size/1e9)
            # if file is only slightly greater than 1 gig make 2 files
            if nfiles == 1:
                nfiles = 2
        else:
            continue

        with open(file, 'r') as f:
            lines = f.readlines()
            nlines = len(lines)

        # get the number of lines to write to each new file
        split_size = int(nlines/nfiles)
        start_index = 0
        # copy old content directly to new smaller files
        for n in range(nfiles):
            with open(file+'.part{}'.format(n), 'w') as f:
                end_index = split_size*(n+1)
                if end_index > nlines:
                    for line in lines[start_index:]:
                        f.write(line)
                    break
                else:
                    for line in lines[start_index:end_index]:
                        f.write(line)
                    start_index += split_size

        # delete the old big file
        os.remove(file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default=None, help='Path to training data')
    parser.add_argument('--output_dir', default=None, help='Output directory for final model')
    args = parser.parse_args()
    preprocess_data(args)
    make_model(args)
    test_model(args)


if __name__ == "__main__":
    main()
