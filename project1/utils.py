import os
import sys

import numpy as np
from collections import Counter
from itertools import islice
import pickle

class Vocab(object):
    def __init__(self):
        '''Stores mappings between words (string) and tokens (integer).
        '''
        self.word_to_index = dict()
        self.index_to_word = dict()
        self.word_counter = Counter()

        self.unknown = '<unk>'
        self.padding = '<pad>'
        self.begin = '<bos>'
        self.end = '<eos>'

    def update(self, sentence):
        '''Update counts with words in sentence.
        '''
        if isinstance(sentence, str):
            self.word_counter.update(sentence.split())
        else:
            assert isinstance(sentence[0], str)
            self.word_counter.update(sentence)
        return

    def construct(self, path, vocab_size):
        '''Construct a vocabulary from path, cutting infrequent words to given size.
        '''
        for line in open(path, 'r'):
            self.update(line)
        for key in [self.unknown, self.padding, self.begin, self.end]:
            self._insert(key)
        if vocab_size is None:
            words = [w for (w, _) in self.word_counter.most_common()]
        else:
            words = [w for (w, _) in self.word_counter.most_common(vocab_size - 4)]
        for w in words:
            self._insert(w)
        return

    def _insert(self, word):
        '''Stores word in the token maps.
        '''
        if not word in self.word_to_index:
            index = len(self.word_to_index)
            self.word_to_index[word] = index
            self.index_to_word[index] = word
        return

    def encode(self, word):
        '''Turn token word into integer index.
        '''
        try:
            index = self.word_to_index[word]
        except KeyError:
            index = self.word_to_index[self.unknown]
        return index

    def decode(self, index):
        '''Turn integer index into token word.
        '''
        return self.index_to_word[index]

class DataReader(object):
    def __init__(self):
        self.vocab = Vocab()
        self.data = None
        self.cache_file = '/tmp/nlp-project-sentences-train.pickle'
        return
    
    def construct(self, path, vocab_size, sent_size):
        '''Load vocabulary, mapping words to tokens, then load corpus as tokens.
        '''
        #if os.path.isfile(self.cache_file):
        #    print('loading cached data from: %s' % self.cache_file)
        #    with open(self.cache_file, 'rb') as f:
        #        self.data, self.vocab = pickle.load(f)
        #else:

        print('constructing data set')

            # intial pass over path to construct vocabulary 
        self.vocab.construct(path, vocab_size)
        
            # second pass to load corpus as tokens
        nsents = sum(1 for line in open(path, 'r'))

            # add padding, bos, eos symbols
        self.data = np.empty((nsents, sent_size), dtype=int)
        self.data.fill(self.vocab.encode(self.vocab.padding))
        self.data[:, 0] = self.vocab.encode(self.vocab.begin)
        self.data[:, -1] = self.vocab.encode(self.vocab.end)
        for indx, line in enumerate(open(path, 'r')):
            tokens = [self.vocab.encode(word) for word in line.split()]
            tokens = tokens[:sent_size - 2]
            self.data[indx, 1:len(tokens)+1] = tokens

        #with open(self.cache_file, 'wb') as f:
        #    pickle.dump((self.data, self.vocab), f)
        print('caching data set here: %s' % self.cache_file)
                
        return

    def _shuffle(self):
        '''Shuffle the rows of self.data.
        '''
        assert self.data is not None
        perm = np.random.permutation(self.data.shape[0])
        self.data = self.data[perm]
        return

    def get_iterator(self, batch_size, shuffle=True):
        '''Iterator yielding batch number, batch_size sentences.
        '''
        if shuffle: self._shuffle()
        counter = 0
        while True:
            batch = islice(self.data, batch_size*counter, batch_size*(counter+1))
            batch = list(batch)
            if batch == []: return
            yield counter, batch
            counter += 1

class SubmissionGenerator(object):

    def __init__(self, submission_folder):
        self.filename = os.path.join(submission_folder, 'group29.perplexity')

    def append_perplexities(self, perplexities):
        with open(self.filename, 'a') as file:
            for perplexity in perplexities[0]:
                file.write(str(perplexity)+'\n')
            file.close()
        print('Appended perplexities to ' + str(self.filename))
