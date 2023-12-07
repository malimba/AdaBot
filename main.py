#imports

#LOGGING
import logging
#for python-telegram-bot package.
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, filters
#for bot configurations
from config import TOKEN

#for bot functions
from bot_functions import start, upload_notes_conv_handler

#for helpers functions
from helpers import CustomPersistence

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def main() -> None:
    #intialise persistence
    # persistence = SQLitePersistence('botdatabase.db')
    # updater = Updater(TOKEN, persistence=persistence, use_context=True)
    
    updater = Updater(TOKEN)

    #CREATE bot dispatcher
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start)) #enable bot respond to start command by processing command per rules in bot_functions.start function rules
    dp.add_handler(upload_notes_conv_handler)

    #start polling to receive bot updates
    updater.start_polling()
    updater.idle()

#run program till key interrupt
if __name__ == '__main__':
    main()
