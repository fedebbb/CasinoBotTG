import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  #Telegram API code

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, write /help to see al the features and games!")

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{user}, Here is the list of the commands:")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand this message.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    #handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    unknown_handler = MessageHandler(filters.TEXT, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()