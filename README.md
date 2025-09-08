# CasinoBotTG 🎰

CasinoBotTG is a Telegram bot that emulates casino games, built using Python and the python-telegram-bot library.
Users can play games like coin flip and roulette, track their balance, and receive daily bonuses.

# 📝 Requirements

Install dependencies with:

pip install -r requirements.txt

Python 3.10+ recommended

python-telegram-bot library

# ⚡ Features / Available Commands
**Command**	**Description**
**/start**	Registers the user and shows a welcome message.
**/help**	Displays a list of available commands and instructions.
**/games**	Shows the list of casino games available.
**/bonus**	Gives the user a daily bonus (every 24 hours).
**/balance**	Shows the user's current balance.
**/coinflip**	Play a coin flip game. Usage: /coinflip <amount>
**/roulette**	Play a roulette game. Usage: /roulette <amount> <choice>. Choices: red, black, odd, even, or a number 0-36.

# 🎲 How to Play
**Coin Flip**

- Use /coinflip <amount> to place your bet.

- Choose Head or Tail either via keyboard or inline buttons.

- The bot will flip the coin and update your balance accordingly.

**Roulette**

1. Use /roulette <amount> <choice> to place a bet.

2. Choices can be:

    - red / black → bets on color

    - odd / even → bets on parity

    - 0-36 → bets on a single number

3. The bot spins the roulette and updates your balance. Special rules: 0 is green and loses for color/parity bets.

4. Payouts:

    - Number: 35:1

    - Color / Odd-Even: 1:1

# 📌 Notes

Users start with a default balance (1000 credits).

Daily bonus is controlled via timestamps in the database.

All data is stored in a local SQLite database (casino.db).

# ⚙️ Installation

1. Clone the repository:
    git clone <https://github.com/fedebbb/CasinoBotTG>

2. Install dependencies:
    pip install -r requirements.txt

3. Add your Telegram Bot TOKEN in bot.py.

4. Run the bot:
    python bot.py