import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from io import BytesIO

from backend.gensim_backend import GensimBackend
from backend.fasttext_backend import FasttextBackend

BACKENDS = {
    "gensim": GensimBackend,
    "fasttext": FasttextBackend
}

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

        self.bot_duel_handler = CommandHandler('duel', self.bot_duel)
        self.dispatcher.add_handler(self.bot_duel_handler)

        self.dispatcher.add_handler(self.text_handler)

        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.switch_backend_callback))

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
                         text="Hey, I'm your game partner. We are both trying to guess the same word." +
                              " Start by typing your initial word and I'll reply with my guess." +
                              " If you are stuck you can restart with /restart")

        keyboard = [[InlineKeyboardButton("gensim", callback_data='gensim')],
                    [InlineKeyboardButton("fasttext", callback_data='fasttext')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=update.message.chat_id, text="Please select backend",
                         reply_markup=reply_markup)

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

    def bot_duel(self, bot, update):
        chat_id = update.effective_chat.id
        gensim_bot = GensimBackend()
        fasttext_bot = FasttextBackend()

        gensim_word = gensim_bot.get_random_word()
        fasttext_word = fasttext_bot.get_random_word()

        for _ in range(15):
            bot.send_message(chat_id=chat_id, text="%s | %s" % (gensim_word, fasttext_word))

            try:
                gensim_word = gensim_bot.get_next_word(gensim_word, fasttext_word)
                fasttext_word = fasttext_bot.get_next_word(gensim_word, fasttext_word)
            except KeyError:
                bot.send_message(chat_id=chat_id, text="The bots got confused. Please start again")
                break


    def restart(self, bot, update):
        chat_id = update.effective_chat.id
        keyboard = [[InlineKeyboardButton("gensim", callback_data='gensim')],
                    [InlineKeyboardButton("fasttext", callback_data='fasttext')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=chat_id, text="Please select backend",
                         reply_markup=reply_markup)

    def switch_backend_callback(self, bot, update):
        query = update.callback_query
        chat_id = query.message.chat_id

        bot.edit_message_text(text="Selected option: {}. You can start entering your word".format(query.data),
                              chat_id=chat_id,
                              message_id=query.message.message_id)

        self.backend_of_user[chat_id] = BACKENDS[query.data]()
        for k, v in self.backend_of_user.items():
            logger.info("%s: %s" % (str(k), str(v)))
        random_word = self.backend_of_user[chat_id].get_random_word()
        self.next_words[chat_id] = random_word
        logger.info("Restarted game with %s id and random word %s" % (chat_id,
                                                                      random_word))


def main():
    with open("token", "r") as f:
        token = f.read().splitlines()[0]

    GameBot(token)


if __name__ == "__main__":
    main()
