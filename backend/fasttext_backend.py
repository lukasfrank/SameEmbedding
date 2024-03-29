from gensim.models.fasttext import FastText
import random
import logging
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

word_vectors = FastText.load_fasttext_format('data/fasttext_de.bin')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FasttextBackend:
    def __init__(self):
        logger.info("Constructed new gensim backend")

        self.word_blacklist = []
        self.user_history_words = []
        self.computer_history_words = []
        self.user_history_vecs = []
        self.computer_history_vecs = []
        self.tsne_model = TSNE(n_components=2)

    def get_random_word(self):
        """
        Return random word from the vocabulary.
        """
        return random.choice(list(word_vectors.wv.vocab.keys()))

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
            user_vec = word_vectors.wv.get_vector(user_word)
            computer_vec = word_vectors.wv.get_vector(computer_word)
        except KeyError:
            logger.warning("%s or %s not found" % (user_word, computer_word))
            raise KeyError

        self.user_history_words.append(user_word)
        self.user_history_vecs.append(user_vec)

        self.computer_history_words.append(computer_word)
        self.computer_history_vecs.append(computer_vec)

        # if len(self.user_history_vecs) == 10:
        #     self.tsne_embedding()

        # Check weighting
        word_list = word_vectors.wv.most_similar(positive=[(user_word, 2.0), (computer_word, 1)], restrict_vocab=10000)
        logger.info(word_list)

        for word, similarity in word_list:
            if word.lower() not in self.word_blacklist:
                return word

    def tsne_embedding(self):
        """
        Calculate t-SNE embedding.

        :return: matplotlib
        """
        tsne_proj = self.tsne_model.fit_transform(np.concatenate((self.user_history_vecs, self.computer_history_vecs)))
        vec_size = len(self.user_history_vecs)
        fig, ax = plt.subplots(1, 1)
        ax.scatter(tsne_proj[:vec_size, 0], tsne_proj[:vec_size, 1], color="green", label="user")
        ax.plot(tsne_proj[:vec_size, 0], tsne_proj[:vec_size, 1], color="green", label="user")
        for i in range(vec_size):
            ax.text(tsne_proj[i, 0], tsne_proj[i, 1], str(i) + " " + self.user_history_words[i])

        ax.scatter(tsne_proj[vec_size:, 0], tsne_proj[vec_size:, 1], color="red", label="computer")
        ax.plot(tsne_proj[vec_size:, 0], tsne_proj[vec_size:, 1], color="red", label="computer")
        for i in range(vec_size):
            ax.text(tsne_proj[vec_size + i, 0], tsne_proj[vec_size + i, 1], str(i) + " " + self.computer_history_words[i])

        ax.legend()
        plt.show()
