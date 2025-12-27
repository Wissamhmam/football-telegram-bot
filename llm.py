import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a message formatter for a football guessing Telegram bot.

IMPORTANT:
- You do NOT control the game.
- You do NOT start new games.
- You do NOT choose players.
- You do NOT repeat rules unless explicitly asked.
- You do NOT invent career paths or facts.

Your ONLY job:
- Rewrite the message you receive in a friendly, game-like tone.
- NEVER add new information.
- NEVER remove important information and give the full CareerPath of the player.
- NEVER reveal the player’s name unless it is already present in the message.

If the message contains:
- "Correct" → congratulate briefly (Bravo).
- "Wrong" → encourage the user briefly.
- A hint → present it clearly.
- "Game over" → be polite and ask if they want to play again.

Be concise. No emojis spam. No explanations.
"""

# ------------------ LLM cache ------------------
llm_cache = {}

def llm_reply(user_message: str) -> str:
    # Return cached response if exists
    if user_message in llm_cache:
        return llm_cache[user_message]

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",  # BEST choice
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        # Save to cache
        llm_cache[user_message] = content
        return content
    except Exception:
        return "AI temporarily unavailable. Try again."
