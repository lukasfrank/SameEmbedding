from gensim.models import KeyedVectors
import random
word_vectors = KeyedVectors.load_word2vec_format('../data/german.model', binary=True)


class GensimBackend:
    def __init__(self):
        self.word_blacklist = []

    def get_random_word(self):
        """
        Return random word from the vocabulary.
        """
        return random.choice(list(word_vectors.vocab.keys()))

    def get_next_word(self, user_word, computer_word):
        """
        Return next word from user_word and computer_word.

        :param user_word: word chosen by user
        :param computer_word: word chosen by computer from the last iteration
        :return:
        """
        self.word_blacklist.append(user_word.lower())
        self.word_blacklist.append(computer_word.lower())

        try:
            word_vectors.get_vector(user_word)
            word_vectors.get_vector(computer_word)
        except KeyError:
            return None

        word_list = word_vectors.most_similar(positive=[user_word, computer_word])

        for word, similarity in word_list:
            if word not in self.world_blacklist:
                return word

