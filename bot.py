import logging
import os
import sqlite3
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  #Telegram API code

#connection to the database SqlLite
conn = sqlite3.connect("casino.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 1000,
    last_bonus TIMESTAMP DEFAULT '2000-01-01T00:00:00'
    )
""")
conn.commit()
conn.close()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = update.effective_user.first_name
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="I'm a bot, write /help to see al the features and games!"
        )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, Here is the list of the commands: \n/bonus : take your daily bonus"
        )

#give the bonus every 24 hours
async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user = update.effective_user.first_name
    time= datetime.datetime.now()
    bonus_amount = 500 #set the daily bonus
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT balance, last_bonus FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    saldo, last_bonus = row
    ora = datetime.datetime.now()  
    ultimo_bonus = datetime.datetime.fromisoformat(last_bonus) 
    delta = ora - ultimo_bonus
    if delta.total_seconds() >= 86400:
        new_balance = saldo + bonus_amount
        c.execute(
            "UPDATE users SET balance=?, last_bonus=? WHERE user_id=?",
            (new_balance, ora.isoformat(), user_id)
        )
        conn.commit()
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text=f"You just earned {bonus_amount} credits! New balance: {new_balance}"
        )
    else:
        last = datetime.datetime.fromisoformat(last_bonus)
        time_last = 86400 - (ora - last).total_seconds()
        h = int(time_last // 3600)
        m = int((time_last % 3600) // 60)
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text=f"You have already taken your daily bonus! Retry in {h}h {m}m."
        )
    
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    c.close()
    balance = row[0] #takes the balance
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, your balance is {balance} credits"
        )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Sorry, I didn't understand this message."
    )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    #handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    bonus_handler = CommandHandler('bonus', bonus)
    application.add_handler(bonus_handler)

    balance_handler = CommandHandler('balance', balance)
    application.add_handler(balance_handler)

    unknown_handler = MessageHandler(filters.TEXT, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()