from __future__ import print_function
from gensim.models.doc2vec import TaggedDocument
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
import numpy as np
import gensim
import time
import sklearn
import helper
import os
import logging
from sklearn.linear_model import LogisticRegression
import multiprocessing
num_cpus = multiprocessing.cpu_count()


class MySentences(object):
    def __init__(self, db, flag, keywords):
        """ Constructor for a sentence, used to create an iterator for better memory usage
        :param db: The Mongodb database
        :param flag: If flag is 1 run it on full papers, else on abstracts
        :return: None, create MySentence instance
        """
        self.db = db
        self.flag = flag
        self.keywords = keywords
        self.sentences = []

    def to_array(self):
        self.sentences = []
        for keyword in self.keywords:
                cursor = self.db.papers.find({'keyword': keyword})
                for item in cursor:
                    if self.flag:
                        text = item['text']
                    else:
                        text = item['abstract']
                    # Convert to utf-8
                    try:
                        text = text.decode('utf8')
                    except UnicodeDecodeError:
                        print('Error decoding ' + text)
                        print(type(text))
                    # Tokenize sentences
                    tokens = sent_tokenize(text)
                    sentence_counter = 0
                    for sent in tokens:
                        word_tokens = word_tokenize(sent)
                        # Append to sentences
                        if word_tokens:
                            self.sentences.append(TaggedDocument(word_tokens, [keyword + '_' + str(sentence_counter)]))
                            sentence_counter += 1
        return self.sentences

    def sentences_perm(self):
        return np.random.permutation(self.sentences)

    def __iter__(self):
        """ Create iterator
        :return: Iterator
        """
        for keyword in self.keywords:
            cursor = self.db.papers.find({'keyword': keyword})
            ids = [item['_id'] for item in cursor]
            for id in ids:
                item = self.db.papers.find_one({'_id': id})
                if self.flag:
                    text = item['text']
                else:
                    text = item['abstract']
                # Convert to utf-8
                try:
                    text = text.decode('utf8')
                except UnicodeDecodeError:
                    print('Error decoding ' + text)
                    print(type(text))
                # tokens = self.word_tokenize(text)
                tokens = sent_tokenize(text)
                sentence_counter = 0
                for sent in tokens:
                    word_tokens = word_tokenize(sent)
                    # Yield the words to Word2Vec
                    if word_tokens:
                        yield TaggedDocument(word_tokens, [keyword + '_' + str(sentence_counter)])
                        sentence_counter += 1


def get_classifier(db, dimension, keywords, model):
    key_count, total_count = 0, 0
    num_documents = db.papers.find().count()
    train_arrays = np.zeros((num_documents, dimension))
    train_labels = np.zeros(num_documents)
    for keyword in keywords:
        cursor = db.papers.find({'keyword': keyword})
        for i in xrange(cursor.count()):
            tag = keyword + '_' + total_count
            train_arrays[total_count] = model[tag]
            train_labels[total_count] = key_count
            total_count += 1
        key_count += 1
    classifier = LogisticRegression(C=1.0, class_weight=None, dual=False, fit_intercept=True,
                                    intercept_scaling=1, penalty='l2', multi_class='ovr', random_state=None, tol=0.0001)
    classifier.fit(train_arrays, train_labels)
    return classifier


def classify(db, dimension, keywords, model, text):
    classifier = get_classifier(db, dimension, keywords, model)
    idx_to_keywords = dict([(i, v) for i, v in enumerate(keywords)])
    vector = model.infer_vector(text)
    probability_vector = classifier.predict_proba(vector)
    return dict([(idx_to_keywords[i], v) for i, v in enumerate(probability_vector)])


def word2vec_clusters(model):
    """ Run k-means clusters on the Word2vec vectors
    :param model: The word2vec
    :return: None
    """
    start = time.time()
    vectors = model.syn0
    num_clusters = int(raw_input('Number of clusters: '))
    print("Running clustering with %d clusters" % num_clusters)
    clustering_algorithm = sklearn.cluster.MiniBatchKMeans(n_clusters=num_clusters)
    idx = clustering_algorithm.fit_predict(vectors)
    end = time.time()
    elapsed = end - start
    print("Time for clustering: ", elapsed, "seconds.")
    centroid_map = dict(zip(model.index2word, idx))
    for cluster in range(num_clusters):
        words = [key for key in centroid_map.keys() if centroid_map[key] == cluster]
        if 1 < len(words) < 20:
            print("\nCluster %d" % cluster)
            print(words)


def build_model(db, flag, cores=num_cpus, num_epochs=10):
    """ Build Word2Vec model
    :param db: The Mongodb database
    :param flag: If flag is 1 then run cluster on full papers, else run on abstracts
    :return: None, call k-means from w2vClusters(corpus)
    """
    # Get keywords
    cursor = db.papers.find()
    keywords = [item['keyword'] for item in cursor]
    sentences = MySentences(db, flag, keywords)
    # For now let the parameters be default
    print("Training doc2vec model using %d cores" % cores)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    model = gensim.models.Doc2Vec(sentences, size=400, min_count=1, window=10, alpha=0.025, min_alpha=0.025,
                                  sample=1e-4, workers=cores)
    model.build_vocab(sentences.to_array())
    for i in xrange(num_epochs):
        model.train(sentences.sentences_perm())
        model.alpha -= 0.002
        model.min_alpha = model.alpha
    # Save model
    model_path = 'model/'
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    cursor = db.papers.find()
    model_name = 'model_' + str(cursor.count()) + '_' + str(num_epochs)
    model.save(model_path + model_name)


def continue_training(db, flag, model_name, cores=num_cpus):
    """ Continue training word2vec model
    :param db: Mongodb database
    :param flag: If flag is 1 then train over full texts
    :param model_path: Path to word2vec model
    :param cores: Number of cores to use
    :return: None
    """
    # Get keywords
    cursor = db.papers.find()
    keywords = [item['keyword'] for item in cursor]
    sentences = MySentences(db, flag, keywords)
    print("Training doc2vec model using %d cores" % cores)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    # Load model from model_path
    model = gensim.models.Doc2Vec.load(model_name)
    # Continue training model
    model.train(sentences)
    # Save the model for future use
    model_path = 'model/'
    if not os.path.exists(model_path):
        os.makedirs(model_path)
    cursor = db.papers.find()
    model_name = 'model_' + str(cursor.count())
    model.save(model_path + model_name)