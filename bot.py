import asyncio
import logging
import sqlite3
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ChatJoinRequestHandler, CallbackQueryHandler, ContextTypes

# ==================== WEB SERVER (For Render) ====================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)
# =================================================================

# ==================== CONFIGURATION ====================
# ⚠️ APNA NAYA TOKEN YAHAN DALEIN
BOT_TOKEN = "8855348170:AAGmLb8y_mrCL9vbTtbQsQye1GW6O0MjnqA" 

# ⚠️ MAIN GROUP KI ID YAHAN DALEIN (Jahan join request aayegi)
MAIN_CHAT_ID = -1004327771945 

# 👇 YAHAN APNE CHANNELS DALEIN (Group/Channel ki ID aur Link) 👇
CHANNELS = [
    {
        "id": -1003802690156,  # <-- Test ke liye apne group ki asli ID yahan dalein
        "link": "https://t.me/+OVSa9g9gR2c2YjI1", 
        "name": "🔊 TEST CHANNEL 🔥"
    }
]
# =======================================================

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== DATABASE SETUP ====================
def setup_db():
    conn = sqlite3.connect("bot_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS verified_users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    return conn, cursor

conn, cursor = setup_db()
# =======================================================

# 1. Start Command (Agar user direct bot me aaye)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check karo verify hua hai ya nahi
    cursor.execute("SELECT * FROM verified_users WHERE user_id = ?", (user_id,))
    is_verified = cursor.fetchone()

    if is_verified:
        await update.message.reply_text("✅ Aap pehle se verified hain. Aap group join kar sakte hain.")
        return

    # Agar verified nahi hai, toh links bhejo
    keyboard = []
    for ch in CHANNELS:
        keyboard.append([InlineKeyboardButton(ch['name'], url=ch['link'])])
    
    keyboard.append([InlineKeyboardButton("✅ I'VE JOINED — VERIFY", callback_data="verify_btn")])
    
    text = (
        "🔒 **ONE LAST STEP**\n\n"
        "Join the channels below to unlock the bot.\n\n"
        "Joined? Tap the button below 👇"
    )
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# 2. Join Request Aane Par
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    req = update.chat_join_request
    user_id = req.from_user.id
    chat_id = req.chat.id
    user_name = req.from_user.first_name

    # User ko group me approve karo
    try:
        await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
    except Exception as e:
        print(f"Error approving: {e}")
        return

    # Check karo verified hai ya nahi
    cursor.execute("SELECT * FROM verified_users WHERE user_id = ?", (user_id,))
    is_verified = cursor.fetchone()

    if is_verified:
        return # Agar pehle se verified hai toh kuch mat karo

    # DM bhejne ki koshish karo
    try:
        keyboard = []
        for ch in CHANNELS:
            keyboard.append([InlineKeyboardButton(ch['name'], url=ch['link'])])
        keyboard.append([InlineKeyboardButton("✅ I'VE JOINED — VERIFY", callback_data="verify_btn")])
        
        text = "🔒 **ONE LAST STEP**\n\nJoin the channels below to unlock the bot.\n\nJoined? Tap the button below 👇"
        
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        print(f"✅ DM sent to {user_id}")
        
    except Exception as e:
        # Agar DM block hai (user ne bot start nahi kiya), toh GROUP me message bhejo
        print(f"❌ DM failed for {user_id}. Sending message to group.")
        
        bot_username = (await context.bot.get_me()).username
        keyboard = [[InlineKeyboardButton("🤖 Verify Here (Click Me)", url=f"https://t.me/{bot_username}?start=verify")]]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 Welcome {user_name}!\n\nInbox me message nahi aaya? Verification karne ke liye neeche diye gaye button par click karein aur bot ko start karein.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# 3. Verify Button Dabane Par
async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer("Checking... ⏳")

    missing_channels = []
    
    for ch in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch['id'], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                missing_channels.append(ch['name'])
        except Exception as e:
            missing_channels.append(ch['name'])
            print(f"❌ CHECK FAILED for {ch['id']}: {e}")

    if len(missing_channels) == 0:
        cursor.execute("INSERT OR IGNORE INTO verified_users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        
        await query.edit_message_text(
            "✅ **Verification Successful!**\n\nAapne channel join kar liya hai. Ab aap group me ja sakte hain."
        )
    else:
        missing_text = "\n".join([f"❌ {ch}" for ch in missing_channels])
        await query.edit_message_text(
            f"⚠️ **Verification Failed!**\n\nAapne abhi ye channel join nahi kiya hai:\n{missing_text}\n\nPehle isko join karein phir dobara VERIFY dabayein.\n\n_(Agar aapne join kar liya hai aur phir bhi error aa raha hai, toh iska matlab Chat ID galat hai ya Bot us channel me Admin nahi hai)_",
            parse_mode="Markdown"
        )

def main():
    # Render ke liye web server start karo
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(CallbackQueryHandler(verify_callback, pattern="verify_btn"))

    print("🤖 Bot Start Ho Gaya Hai...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
