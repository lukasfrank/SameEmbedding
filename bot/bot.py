import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
from io import BytesIO

from backend.base_backend import BaseBackend
from backend.gensim_backend import GensimBackend

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GameBot:
    """
    Telegram Bot providing the "find-the-same-word" game.

    Assumes a file "token", in the base dir.
    """
    def __init__(self, token):
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher

        # collect next word per chat_id
        self.next_words = {}

        # saves backends of users
        self.backend_of_user = {}

        # Handle regular text messages
        self.text_handler = MessageHandler(Filters.text, self.message_reply)

        # Initial start command
        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.start_handler)

        self.restart_handler = CommandHandler('restart', self.restart)
        self.dispatcher.add_handler(self.restart_handler)

        self.tsne_handler = CommandHandler('viz', self.send_tsne)
        self.dispatcher.add_handler(self.tsne_handler)

        self.dispatcher.add_handler(self.text_handler)

        self.updater.start_polling()
        self.updater.idle()

    def start(self, bot, update):
        """
        Initial command, required for setting the chat_id.{} - Iteration: {}, Value: {}".format(
            scalar_name, last_iteration, last_value)

        :param bot:
        :param update:
        :return:
        """
        bot.send_message(chat_id=update.message.chat_id,
                         text="Hey, I'm your game partner. Start by typing your initial word.")

        self.backend_of_user[update.message.chat_id] = GensimBackend()

        random_word = self.backend_of_user[update.message.chat_id].get_random_word()
        self.next_words[update.message.chat_id] = random_word
        logger.info("Intialized new chat with %s id and random word %s" % (update.message.chat_id,
                                                                           random_word))

    def message_reply(self, bot, update):
        """
        Handle messages that are not commands.
        User sends his word and bot replies with his prediction
        """
        user_input = update.message.text
        logger.info("Got user input '%s' " % user_input)
        chat_id = update.effective_chat.id
        computer_word = self.next_words[chat_id]

        # Reply with word calculated in last session
        try:
            if computer_word == user_input:
                # you won and will get an image of the word embedding
                bot.send_message(chat_id=chat_id, text="You won! Good job.")
                self.send_tsne(bot, update, computer_word)
                return

            # Calculate next_word before creating output as we could still fail here
            next_word = self.backend_of_user[chat_id].get_next_word(user_input, computer_word)
            self.next_words[chat_id] = next_word

            response = "*Bot:* %s  *Du:* %s" % (computer_word.replace("_", " "), user_input.replace("_"," "))
            bot.send_message(chat_id=chat_id, text=response, parse_mode=telegram.ParseMode.MARKDOWN)

        except KeyError:
            bot.send_message(chat_id=chat_id, text="Please enter a new word, I don't know yours")

    def send_tsne(self, bot, update, final_word=None):
        chat_id = update.effective_chat.id
        fig, ax = self.backend_of_user[chat_id].tsne_embedding(final_word)

        bio = BytesIO()
        bio.name = 'image.jpeg'
        fig.savefig(bio)
        bio.seek(0)
        bot.send_photo(chat_id, photo=bio)

    def restart(self, bot, update):
        bot.send_message(chat_id=update.message.chat_id,
                         text="Alright, let's play again!")

        self.backend_of_user[update.message.chat_id] = GensimBackend()
        random_word = self.backend_of_user[update.message.chat_id].get_random_word()
        self.next_words[update.message.chat_id] = random_word
        logger.info("Restarted game with %s id and random word %s" % (update.message.chat_id,
                                                                      random_word))


def main():
    with open("token", "r") as f:
        token = f.read().splitlines()[0]

    GameBot(token)


if __name__ == "__main__":
    main()
