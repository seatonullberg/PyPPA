import gensim
import time
import os


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


print('Start Time: {}'.format(time.ctime()))
model = gensim.models.word2vec.Word2Vec(sentences=MemSafeCorpusIterator('text/wiki'), workers=4, size=100)
print('Trained at: {}'.format(time.ctime()))
print(model.wv.most_similar('food'))
model.save('wiki.model')
print({'Saved at: {}'.format(time.ctime())})
model = None
model = gensim.models.word2vec.Word2Vec.load('wiki.model')
print(model.wv.most_similar('food'))
