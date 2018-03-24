
class BaseBackend:
    """
    Abstract Base backend for word embedding models
    """

    def get_random_word(self):
        """
        Return random word from the vocabulary.
        """
        pass

    def get_next_word(self, user_word, computer_word):
        """
        Return next word from user_word and computer_word.

        :param user_word: word chosen by user
        :param computer_word: word chosen by computer from the last iteration
        :return:
        """
        pass