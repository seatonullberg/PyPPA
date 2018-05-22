'''
Initial version of sentence model generation
'''
import gensim
import os
from tqdm import tqdm
import argparse


class MemSafeIterator(object):

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def __iter__(self):
        for fname in os.listdir(self.data_dir):
            print('Iterating over: {}'.format(fname))
            pbar = tqdm(total=len(open(os.path.join(self.data_dir, fname), 'r').readlines()), unit=' lines')
            sentences_to_yield = []
            for line in open(os.path.join(self.data_dir, fname), 'r').readlines():
                # when there is a break in the text treat it as a separation point and yield
                if line == '\n':
                    yield sentences_to_yield
                    sentences_to_yield = []
                else:
                    # add to the ist of sentences
                    sentences_to_yield.append(line.replace('\n', ''))
                pbar.update(1)
            pbar.close()
        print('\n')


def make_model(args):
    data_dir = args.data_dir
    WORKERS = 8
    VEC_SIZE = 300
    MIN_COUNT = 2
    MAX_VOCAB = None
    ITER = 4
    print('Constructing sentence model...\nEach input file will be iterated over {} times.\n'.format(ITER+1))
    model = gensim.models.word2vec.Word2Vec(sentences=MemSafeIterator(data_dir=data_dir),
                                            workers=WORKERS,
                                            size=VEC_SIZE,
                                            min_count=MIN_COUNT,
                                            max_vocab_size=MAX_VOCAB,
                                            iter=ITER)
    model.save(os.path.join(args.output_dir, 'sentence.model'))
    print('Saved new model.')
    print('Vocabulary Size: {}'.format(len(model.wv.vocab)))


def test_model(args):
    model = gensim.models.Word2Vec.load(args.model_path)
    test_sentences = model.wv.index2word[10:20]
    for sentence in test_sentences:
        print(sentence)
        print(model.wv.most_similar(sentence))
        print('\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', default=None, help='Path to training data')
    parser.add_argument('--output_dir', default=None, help='Output directory for final model')
    parser.add_argument('--model_path', default=None, help='Path to the pre-trained sentence model')
    args = parser.parse_args()
    if args.model_path is None:
        make_model(args)
    else:
        test_model(args)


if __name__ == "__main__":
    main()
