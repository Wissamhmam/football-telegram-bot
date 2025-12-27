import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from game import pick_player, is_correct_guess, get_hint, df
from llm import llm_reply

# --------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

user_games = {}
MAX_ATTEMPTS = 5
HINT_START_AT = 3
MAX_HINTS = 2

# --------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player = pick_player()
    user_games[update.effective_user.id] = {
        "player": player,
        "attempts": 0,
        "hints_given": 0,
    }

    intro = (
        f"🎯 Guess the football player from this transfer path:\n\n"
        f"{player['CareerPath']}\n\n"
        f"You have {MAX_ATTEMPTS} guesses.\n"
        f"Hints start after {HINT_START_AT} wrong guesses.\nGood luck!"
    )

    await update.message.reply_text(llm_reply(intro))

# --------------------------------------------------
async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_games:
        await update.message.reply_text("No active game. Type /start to play.")
        return

    player = user_games[user_id]["player"]

    msg = (
        f"⏭️ You skipped this player.\n\n"
        f"The correct answer was: {player['Name']}\n\n"
        f"Type /start to play again!"
    )

    await update.message.reply_text(llm_reply(msg))
    del user_games[user_id]

# --------------------------------------------------
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_games:
        await update.message.reply_text("Type /start to begin a new game.")
        return

    game = user_games[user_id]
    player = game["player"]
    game["attempts"] += 1
    user_guess = update.message.text.strip()

    correct, score, matched_name = is_correct_guess(
        user_guess, player["Name"], df=df
    )

    # ✅ CORRECT
    if correct:
        msg = (
            f"✅ Bravo! You guessed it right: {matched_name}\n"
            f"Do you want to play again? Type /start"
        )
        await update.message.reply_text(llm_reply(msg))
        del user_games[user_id]
        return

    # ❌ WRONG
    remaining = MAX_ATTEMPTS - game["attempts"]

    hint_text = ""
    if game["attempts"] >= HINT_START_AT and game["hints_given"] < MAX_HINTS:
        hint_text = f"\nHint: {get_hint(player, game['hints_given'] + 1)}"
        game["hints_given"] += 1

    very_close = ""
    if score > 0.65:
        very_close = f"\n⚠️ Very close! Maybe you mean: {matched_name}"

    if game["attempts"] >= MAX_ATTEMPTS:
        msg = (
            f"❌ Wrong guess.{very_close}{hint_text}\n\n"
            f"Game over. The correct answer was: {player['Name']}\n"
            f"Do you want to play again? Type /start"
        )
        await update.message.reply_text(llm_reply(msg))
        del user_games[user_id]
        return

    msg = f"❌ Wrong guess.{very_close}{hint_text}\nRemaining guesses: {remaining}"
    await update.message.reply_text(llm_reply(msg))

# --------------------------------------------------
logging.basicConfig(level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skip", skip))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    app.run_polling()

if __name__ == "__main__":
    main()
