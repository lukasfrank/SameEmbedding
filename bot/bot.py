import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging

from backend.base_backend import BaseBackend

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
        self.dispatcher = self.updater.dispatcher
        self.backend = BaseBackend()

        # collect next word per chat_id
        self.next_words = {}

        # Handle regular text messages
        self.text_handler = MessageHandler(Filters.text, self.message_reply)

        # Initial start command
        self.start_handler = CommandHandler('start', self.start)
        self.dispatcher.add_handler(self.start_handler)
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

        random_word = self.backend.get_random_word()
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
        bot.send_message(chat_id=chat_id, text=computer_word)
        self.next_words[chat_id] = self.backend.get_next_word(user_input, computer_word)


def main():
    with open("token", "r") as f:
        token = f.read().splitlines()[0]

    GameBot(token)


if __name__ == "__main__":
    main()
