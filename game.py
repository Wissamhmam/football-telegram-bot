import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Load CSV
df = pd.read_csv("football_players_full.csv")

# Clean data
for col in ["Name", "Country", "Position", "CareerPath", "Nickname"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    else:
        df[col] = ""

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Precompute embeddings once
df["name_embedding"] = list(model.encode(df["Name"].tolist(), normalize_embeddings=True))

# Pick a random player
def pick_player():
    row = df.sample(1).iloc[0]
    return {
        "Name": row["Name"],
        "CareerPath": row["CareerPath"],
        "Position": row["Position"],
        "Nationality": row["Country"],
        "BirthYear": row["BirthYear"] if "BirthYear" in row else "",
        "Nickname": row["Nickname"]
    }

# Get hint based on attempt
def get_hint(player, attempt):
    hints = [
        f"Position: {player['Position']}",
        f"Nationality: {player['Nationality']}",
        f"Born in: {player['BirthYear']}" if player["BirthYear"] else ""
    ]
    return hints[attempt - 1] if attempt <= len(hints) else None

# Check if guess is correct or very close
def is_correct_guess(guess, target_name, df, threshold=0.72, top_k=2):
    guess = guess.strip().lower()
    # Check nicknames first
    matched_nick = df[df["Nickname"].str.lower() == guess]
    if not matched_nick.empty:
        return True, 1.0, matched_nick.iloc[0]["Name"]

    # Compute embedding
    guess_emb = model.encode([guess], normalize_embeddings=True)
    similarities = cosine_similarity(guess_emb, np.vstack(df["name_embedding"]))[0]

    # Top K matches
    top_indices = similarities.argsort()[-top_k:][::-1]
    for idx in top_indices:
        matched_name = df.iloc[idx]["Name"]
        score = similarities[idx]

        if matched_name.lower() == target_name.lower() and score >= threshold:
            return True, score, matched_name

    # Very close feedback
    best_idx = similarities.argmax()
    return False, similarities[best_idx], df.iloc[best_idx]["Name"]
