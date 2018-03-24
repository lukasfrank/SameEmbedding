from gensim.models import KeyedVectors
import random
import logging

word_vectors = KeyedVectors.load_word2vec_format('data/german.model', binary=True)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GensimBackend:
    def __init__(self):
        logger.info("Constructed new gensim backend")

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
            logger.warning("%s or %s not found" % (user_word, computer_word))
            raise KeyError

        # Check weighting
        word_list = word_vectors.most_similar(positive=[(user_word, 2.0), (computer_word, 1)], restrict_vocab=10000)
        logger.info(word_list)

        for word, similarity in word_list:
            if word.lower() not in self.word_blacklist:
                return word

