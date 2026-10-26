import asyncio
import logging
import sqlite3
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ChatJoinRequestHandler, CallbackQueryHandler, ContextTypes

# ==================== WEB SERVER ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)
# ===================================================

# ==================== CONFIGURATION ====================
# ⚠️ APNA TOKEN YAHAN DALEIN
BOT_TOKEN = "8855348170:AAGmLb8y_mrCL9vbTtbQsQye1GW6O0MjnqA" 

# ⚠️ MAIN CHANNEL KI ID YAHAN DALEIN (Jahan join request aayegi)
MAIN_CHAT_ID = 5499608666 

# 👇 TESTING KE LIYE 1 CHANNEL SET KIYA HAI 👇
CHANNELS = [
    {
        "id": 5405589871,  # <-- Yahan Private Channel ki -100 wali ID aayegi
        "link": "https://t.me/+rUbW4Jz-gCdmNzE1", 
        "name": "🔊 TEST CHANNEL 🔥"
    }
]
# =======================================================

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== DATABASE ====================
def setup_db():
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS verified_users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    return conn, cursor

conn, cursor = setup_db()
# =======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot active hai. Main channel par join request bhejein.")

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user_id = req.from_user.id
    chat_id = req.chat.id

    # Agar request MAIN CHANNEL se aayi hai
    if chat_id == MAIN_CHAT_ID:
        cursor.execute("SELECT * FROM verified_users WHERE user_id = ?", (user_id,))
        is_verified = cursor.fetchone()

        try:
            await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            
            if not is_verified:
                keyboard = []
                for ch in CHANNELS:
                    keyboard.append([InlineKeyboardButton(ch['name'], url=ch['link'])])
                
                keyboard.append([InlineKeyboardButton("✅ I'VE JOINED — VERIFY", callback_data="verify_btn")])
                
                text = (
                    "🔒 **ONE LAST STEP**\n\n"
                    "Join the channel below to unlock the bot.\n\n"
                    "Joined? Tap the button below 👇"
                )
                
                await context.bot.send_message(
                    chat_id=user_id, text=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Error main channel approve/DM: {e}")

    # Agar request FORCED (Private) CHANNEL se aayi hai
    else:
        try:
            await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            print(f"✅ Auto-approved user {user_id} in forced channel {chat_id}")
        except Exception as e:
            print(f"Error forced channel approve: {e}")

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer("Checking... ⏳")

    missing_channels = []
    
    for ch in CHANNELS:
        try:
            # Check karo user joined hai ya nahi
            member = await context.bot.get_chat_member(chat_id=ch['id'], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                missing_channels.append(ch['name'])
        except Exception as e:
            # Agar ID galat hai ya bot admin nahi hai, toh error aayega
            missing_channels.append(ch['name'])
            print(f"❌ CHECK FAILED for {ch['id']}: {e}")

    if len(missing_channels) == 0:
        cursor.execute("INSERT OR IGNORE INTO verified_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        
        await query.edit_message_text(
            "✅ **Verification Successful!**\n\nAapne channel join kar liya hai. Ab aap aage badh sakte hain."
        )
    else:
        missing_text = "\n".join([f"❌ {ch}" for ch in missing_channels])
        await query.edit_message_text(
            f"⚠️ **Verification Failed!**\n\nAapne abhi ye channel join nahi kiya hai:\n{missing_text}\n\nPehle isko join karein phir dobara VERIFY dabayein.\n\n_(Agar aapne join kar liya hai aur phir bhi error aa raha hai, toh iska matlab Chat ID galat hai ya Bot us channel me Admin nahi hai)_",
            parse_mode="Markdown"
        )

def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_btn"))

    print("🤖 Testing Bot Start Ho Gaya Hai...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
