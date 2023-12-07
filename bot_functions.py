#! bot_functions.py - This file contains functions necessary for the basic
#                     functions of the bot.

#imports
#for python-telegram-bot package.
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, Filters, CommandHandler, MessageHandler
from helpers import CustomPersistence, Notes
import json
#GLOBALS


#INITILIZE CUSTOM PERSISTENCE CLASS
persistence = CustomPersistence()
notesInstance = Notes('custom_persistence.db')
'''BOT FUNCTIONS DEFINED BELOW'''
#function to respond to /start command of bot, this command returns None data type
def start(update:Update, context:CallbackContext) -> None:
    #reply user's /start command
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    user_data = context.user_data
    user_data['username'] = username
    #Store username in SQLite db using SQLite Persistence class
    # context.persistence.update_user_data(user_id, user_data, content)
    user_exists = persistence.initialize_user(user_id, username)
    if user_exists:
        context.user_date = persistence.load_user_data(user_id)
        update.message.reply_text(f'Hmm, seems like you already have an account {username}')    
    else:
        update.message.reply_text(f'Hello {username}! I am AdaBot.\n My main objective is to help you create tailored learning plan based on notes from each of your lectures.\nI was recently made so I am not that advanced but with time, I\'ll be able to do so much more!\n')

#functions to receive note and process notes
'''
Functions to Be Defined
uploadNotes - handle notes upload
processNotes - process notes return Notes Uploaded message
listTopics - list topics
listLessonPlans - list all Lesson Plans
'''
RETURNVARIABLE = range(1)

def uploadNotes(update:Update, context:CallbackContext) -> int:
    update.message.reply_text('Please send the notes below:')
    return RETURNVARIABLE

def receiveNotes(update:Update, context:CallbackContext) -> int:
    user_id = update.message.from_user.id
    notes = update.message.text
    update.message.reply_text(f'Received your notes {update.message.from_user.username}! Processing...')
    #start saving notes to database
    persistence.save_note(update.message.from_user.id, notes)
    #start Notes porcessing
    lesson_plan = notesInstance.process_notes(notes, user_id)
    print(lesson_plan)
    #send lesson plan to user
    update.message.reply_text('Here\'s your lesson plan')
    pretty_topics = {f'Topic {day}': topic['topic'] for day, topic in lesson_plan.items()}
    pretty_topics_text = json.dumps(pretty_topics, indent=2)

    update.message.reply_text(f'Here\'s your lesson plan: \n\n{pretty_topics_text}')
    return ConversationHandler.END



#cancel function to cancel conversationHandler
def cancel(update:Update, context:CallbackContext) -> int:
    update.message.reply_text('Cancelled')
    return ConversationHandler.END

#Conversation Handler For uploading notes
upload_notes_conv_handler = ConversationHandler(
    entry_points = [CommandHandler('upload_notes', uploadNotes)],
    states = {
        RETURNVARIABLE: [MessageHandler(Filters.text & ~Filters.command, receiveNotes)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

    

