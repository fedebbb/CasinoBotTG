import logging
import os
import sqlite3
import datetime
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  #Telegram API code

SCELTA = range(1)
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
        text=f"{user}, here is the list of the commands: \n/bonus : take your daily bonus \n/balance : see your current balance \n/games: see the games"
        )

#gives the bonus every 24 hours
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

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, here is the list of the games: \n/coinflip <import>"
        )

async def coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #if there arent arguments
    if not context.args:
        await update.message.reply_text("You have to add the bet! For example: /bet 100")
        return
    #if there are more then one argument
    if len(context.args) > 1:
        await update.message.reply_text("Correct use: /coinflip <import>")
        return
    try:
        amount = int(context.args[0])  # first argument
    except ValueError:
        await update.message.reply_text("The import must be a number!")
        return
    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    c.close()
    balance = row[0] #takes the balance
    if balance < amount:
        await update.message.reply_text("You don't have enough credits!")
        return
    context.user_data["amount"] = amount
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, choose between head or tail"
        )
    return SCELTA

async def scelta(update, context):
    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    user_choice = update.message.text.lower().strip()
    if user_choice not in ["head", "tail"]:
        await update.message.reply_text("You have to choose head or tail.")
        return SCELTA
    amount = context.user_data.get("amount", 0)
    #random choice
    result = random.choice(["head", "tail"])
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    amount2 = amount * 2
    if user_choice == result:
        await update.message.reply_text(f"It's {result}! You have won {amount2} credits!")
        c.execute("UPDATE users SET balance = balance + ? * 2 WHERE user_id=?", (amount, user_id,))
    else:
        await update.message.reply_text(f"It's {result}! You have lost {amount} credits...")
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
    conn.commit()
    conn.close()
    return ConversationHandler.END

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

    games_handler = CommandHandler('games', games)
    application.add_handler(games_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("coinflip", coinflip)],
        states={
            SCELTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, scelta)],
        },
        fallbacks = [],
    )
    application.add_handler(conv_handler)

    unknown_handler = MessageHandler(filters.TEXT, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()