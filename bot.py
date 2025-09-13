import logging
import os
import sqlite3
import datetime
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  #Telegram API code

SCELTA = range(1)
SCELTA1 = range(1)
SCELTA2 = range(1)
SCELTA3 = range(1)

#connection to the database SqlLite
conn = sqlite3.connect("casino.db")
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
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
    c.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?,?)", (user_id, user,))
    conn.commit()
    conn.close()
    keyboard = [                #start buttons
        ["/help", "/games"], 
        ["/bonus", "/balance"], 
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True,   
        one_time_keyboard=False 
    )
    await update.message.reply_text(
        "I'm a bot, write /help to see al the features and games!",
        reply_markup=reply_markup
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, here is the list of the commands: \n/bonus : take your daily bonus \n/balance : see your current balance \n/games: see the games \n/leaderboard: see the top10 players"
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
            text=f"You just earned {bonus_amount} credits💵 💰! New balance: {new_balance}"
        )
    else:
        last = datetime.datetime.fromisoformat(last_bonus)
        time_last = 86400 - (ora - last).total_seconds()
        h = int(time_last // 3600)
        m = int((time_last % 3600) // 60)
        conn.close()
        await context.bot.send_message(
            chat_id=user_id,
            text=f"You have already taken your daily bonus! Retry in {h}h {m}m. ⏰⏰"
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
        text=f"{user}, your balance is {balance} credits 💵"
        )

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"{user}, here is the list of the games: \n- /coinflip <amount> \n- /roulette <amount> \n- /blackjack <amount>" 
        )

async def coinflip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #if there arent arguments
    if not context.args:
        await update.message.reply_text("⚠️ You have to add the bet! For example: /coinflip 100")
        return
    #if there are more then one argument
    if len(context.args) > 1:
        await update.message.reply_text("Correct use: /coinflip <amount>")
        return
    try:
        amount = int(context.args[0])  # first argument
    except ValueError:
        await update.message.reply_text("⚠️ The import must be a number!")
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
        text=f"✅ {user}, choose between head or tail"
        )
    return SCELTA

async def sceltaFlip(update, context):
    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    user_choice = update.message.text.lower().strip()
    if user_choice not in ["head", "tail"]:
        await update.message.reply_text("⚠️ You have to choose head or tail.")
        return SCELTA
    amount = context.user_data.get("amount", 0)
    #random choice
    result = random.choice(["head", "tail"])
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    amount2 = amount * 2
    if user_choice == result:
        await update.message.reply_text(f"It's {result}! You have won {amount2} credits! 🎉💰")
        c.execute("UPDATE users SET balance = balance + ? * 2 WHERE user_id=?", (amount, user_id,))
    else:
        await update.message.reply_text(f"😢 It's {result}! You have lost {amount} credits...")
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
    conn.commit()
    conn.close()
    return ConversationHandler.END

async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #if there arent arguments
    if not context.args:
        await update.message.reply_text("⚠️ You have to add the bet! For example: /roulette 100")
        return
    #if there are more then one argument
    if len(context.args) > 1:
        await update.message.reply_text("Correct use: /roulette <amount>")
        return
    try:
        amount = int(context.args[0])  # first argument
    except ValueError:
        await update.message.reply_text("⚠️ The import must be a number!")
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
        text=f"✅ {user}, place a bet."
        )
    return SCELTA

async def sceltaRoulette(update, context):
    RED_NUMBERS = {
    1,3,5,7,9,12,14,16,18,
    19,21,23,25,27,30,32,34,36
    }
    BLACK_NUMBERS = {
        2,4,6,8,10,11,13,15,17,
        20,22,24,26,28,29,31,33,35
    }

    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    user_choice = update.message.text.lower().strip()
    valid_choices = ["red", "black", "odd", "even"]
    if user_choice in valid_choices:
        pass
    else:
        try:
            number = int(user_choice)
            if 0 <= number <= 36:  #valid choice
                pass
            else:
                await update.message.reply_text("⚠️ You must choose red, black, odd, even or a number between 0 and 36.")
                return
        except ValueError:
            await update.message.reply_text("⚠️ You must choose red, black, odd, even or a number between 0 and 36.")
            return
    amount = context.user_data.get("amount", 0)
    #random choice
    result = random.randint(0, 36)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    if user_choice in ["red", "black"]:
        if result in BLACK_NUMBERS:
            color = "black"
        elif result in RED_NUMBERS:
            color = "red"
        else:
            color = "green"
        if color == user_choice :
            await update.message.reply_text(f"🎰 The roulette landed on {result}, it's {color}! You have won {amount*2} credits! 🎉💰")
            c.execute("UPDATE users SET balance = balance + ? * 2 WHERE user_id=?", (amount, user_id,))
        else:
            await update.message.reply_text(f"🎰 The roulette landed on {result}, it's {color}! You have lost {amount} credits...")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
    elif user_choice in ["odd" , "even"] :
        is_even = ((result % 2 ) == 0)
        if is_even and result != 0:
            parity = "even"
        elif result!= 0:
            parity = "odd"
        else: parity = "zero"
        if parity == user_choice :
            await update.message.reply_text(f"🎰 The roulette landed on {result}, it's {parity}! You have won {amount*2} credits! 🎉💰")
            c.execute("UPDATE users SET balance = balance + ? * 2 WHERE user_id=?", (amount, user_id,))
        elif result == 0:
            await update.message.reply_text(f"🎰 The roulette landed on {result}! You have lost {amount} credits...😢 ")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
        else:
            await update.message.reply_text(f"🎰 The roulette landed on {result}, it's {parity}! You have lost {amount} credits...😢 ")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
    else:
        if result == user_choice :
            await update.message.reply_text(f"🎰 The roulette landed on {result}! You have won {amount*36} credits! 🎉💰")
            c.execute("UPDATE users SET balance = balance + ? * 36 WHERE user_id=?", (amount, user_id,))
        else:
            await update.message.reply_text(f"🎰 The roulette landed on {result}! You have lost {amount} credits...😢 ")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
    conn.commit()
    conn.close()
    return ConversationHandler.END

async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suits = ["Spades♠️", "Hearts♥️", "Diamonds♦️", "Clubs♣️"] 
    ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]

    #52 cards deck
    deck = [(rank, suit) for suit in suits for rank in ranks]
    random.shuffle(deck)
    context.user_data["deck"] = deck

    user_hand = []
    user_hand.append(deck.pop())
    user_hand.append(deck.pop())
    context.user_data["user_hand"] = user_hand

    dealer_hand = []
    dealer_hand.append(deck.pop())
    dealer_hand.append(deck.pop())
    context.user_data["dealer_hand"] = dealer_hand

    #if there arent arguments
    if not context.args:
        await update.message.reply_text("⚠️ You have to add the bet! For example: /blackjack 100")
        return
    #if there are more then one argument
    if len(context.args) > 1:
        await update.message.reply_text("Correct use: /blackjack <import>")
        return
    try:
        amount = int(context.args[0])  # first argument
    except ValueError:
        await update.message.reply_text("⚠️ The import must be a number!")
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
    card = dealer_hand[0]
    rank=card[0]
    suit = card[1]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Dealer's hand: {rank} of {suit}"
        )
    card1 = user_hand[0]
    rank1 = card1[0]
    suit1 = card1[1]
    card2 = user_hand[1]
    rank2 = card2[0]
    suit2 = card2[1]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Your's hand: {rank1} of {suit1} and {rank2} of {suit2}"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"✅ {user}, stand or hit?"
        )
    return SCELTA2

async def sceltaBlackjack(update, context):
    user = update.effective_user.first_name
    user_id = update.effective_chat.id
    user_choice = update.message.text.lower().strip()
    valid_choices = ["stand", "hit"]
    if user_choice in valid_choices:
        pass
    else:
        await update.message.reply_text("⚠️ You must choose between hit or stand.")
        return

    amount = context.user_data.get("amount", 0)
    deck = context.user_data.get("deck", 0)
    user_hand = context.user_data.get("user_hand", 0)
    dealer_hand = context.user_data.get("dealer_hand", 0)

    if user_choice == "hit":
        new_card = deck.pop()
        user_hand.append(new_card)
        new_rank = new_card[0]
        new_suit = new_card[1]
        context.user_data["user_hand"] = user_hand

        user_points = 0
        for rank,suit in user_hand:
            if rank.lower() in ["jack", "queen", "king"]:
                user_points += 10
            elif rank == "A" and (user_points+11>21):
                user_points += 1
            elif rank == "A" and (user_points+11<=21):
                user_points += 11
            else:
                points = int(rank)
                user_points += points

        if user_points > 21:
            conn = sqlite3.connect("casino.db")
            c = conn.cursor()
            await update.message.reply_text(f"🎰 You got {new_rank} of {new_suit}. Total points: {user_points}. You have lost {amount} credits...😢")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
            conn.commit()
            conn.close()
            return ConversationHandler.END
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"🎴 {user}, you just got a {new_rank} of {new_suit}. Your points: {user_points}"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"✅ {user}, stand or hit?"
        )
        return SCELTA3
    else:
        user_points = 0
        for rank,suit in user_hand:
            if rank.lower() in ["jack", "queen", "king"]:
                user_points += 10
            elif rank == "A" and (user_points+11>21):
                user_points += 1
            elif rank == "A" and (user_points+11<=21):
                user_points += 11
            else:
                points = int(rank)
                user_points += points
        dealer_points = 0
        for rank,suit in dealer_hand:
            if rank.lower() in ["jack", "queen", "king"]:
                dealer_points += 10
            elif rank == "A" and (dealer_points+11>21):
                dealer_points += 1
            elif rank == "A" and (dealer_points+11<=21):
                dealer_points += 11
            else:
                points = int(rank)
                dealer_points += points
        if user_points <21:
            second_card = dealer_hand[1]
            sRank, sSuit = second_card
            await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=f"🃏The dealer's second card is {sRank} of {sSuit}. Total now: {dealer_points}"
            )
            while(dealer_points<17):
                card1 = deck.pop()
                rank = card1[0]
                suit = card1[1]
                dealer_hand.append(card1)
                if rank.lower() in ["jack", "queen", "king"]:
                        dealer_points += 10
                elif rank == "A" and (dealer_points+11>21):
                    dealer_points += 1
                elif rank == "A" and (dealer_points+11<=21):
                    dealer_points += 11
                else:
                    points = int(rank)
                    dealer_points += points
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, 
                    text=f"🎯The dealer got a {rank} of {suit}. Total now: {dealer_points}"
                )
        if user_points == 21 and len(user_hand) == 2 and len(dealer_hand) > 2:
            result = "blackjack"
        elif user_points > 21:
            result = "defeat"
        elif dealer_points > 21:
            result = "victory"
        elif user_points == dealer_points:
            result="push"
        elif dealer_points > user_points:
            result = "defeat"
        else:
            result = "victory"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text=f"♣️ {user}, your points: {user_points}, dealer points: {dealer_points}"
        )

        conn = sqlite3.connect("casino.db")
        c = conn.cursor()
        if result == "blackjack":
            await update.message.reply_text(f"🎰 Blackjack!🎉🎉 You have won {amount*1.5} credits! 💰")
            c.execute("UPDATE users SET balance = balance + ? * 1.5 WHERE user_id=?", (amount, user_id,))
        elif result == "victory":
            await update.message.reply_text(f"🎰 It's a win! You have won {amount} credits! 🎉💰")
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id,))
        elif result == "defeat":
            await update.message.reply_text(f"🎰 You have lost {amount} credits...😢")
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id,))
        else:
            await update.message.reply_text(f"🤝 Push! Your total matches the dealer's. Your bet is returned.")

        conn.commit()
        conn.close()
        return ConversationHandler.END

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, balance FROM users ORDER BY balance DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    if not rows:   #no users
        await update.message.reply_text("📊 No players in the leaderboard yet!")
        return
    leaderboard_text = "🏆 Top 10 Players 🏆\n\n"
    for i, row in enumerate(rows, start=1):
        username = row[0] if row[0] else "Unknown"
        balance = row[2]
        name = row[1]
        leaderboard_text += f"{i}. {name} : 💰 {balance} credits\n"
    await update.message.reply_text(leaderboard_text)

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

    leaderboard_handler = CommandHandler('leaderboard', leaderboard)
    application.add_handler(leaderboard_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("coinflip", coinflip)],
        states={
            SCELTA: [MessageHandler(filters.TEXT & ~filters.COMMAND, sceltaFlip)],
        },
        fallbacks = [],
    )
    application.add_handler(conv_handler)

    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler("roulette", roulette)],
        states={
            SCELTA1: [MessageHandler(filters.TEXT & ~filters.COMMAND, sceltaRoulette)],
        },
        fallbacks = [],
    )
    application.add_handler(conv_handler2)

    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler("blackjack", blackjack)],
        states={
            SCELTA2: [MessageHandler(filters.TEXT & ~filters.COMMAND, sceltaBlackjack)],
        },
        fallbacks = [],
    )
    application.add_handler(conv_handler3)

    conv_handler4 = ConversationHandler(
        entry_points=[CommandHandler("sceltaBlackjack", sceltaBlackjack)],
        states={
            SCELTA3: [MessageHandler(filters.TEXT & ~filters.COMMAND, sceltaBlackjack)],
        },
        fallbacks = [],
    )
    application.add_handler(conv_handler4)

    unknown_handler = MessageHandler(filters.TEXT, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()