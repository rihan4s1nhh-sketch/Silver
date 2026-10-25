import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ChatJoinRequestHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = "8637298706:AAFFaJWyUYkZAuJcZKW_a2Yjno8hgiWCOEc"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working! Auto-approve is ON")

async def auto_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        req = update.chat_join_request
        user = req.from_user
        chat = req.chat
        await context.bot.approve_chat_join_request(
            chat_id=chat.id,
            user_id=user.id
        )
        print(f"✅ {user.first_name} approved in {chat.title}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatJoinRequestHandler(auto_approve))

    print("🤖 Zack Bot running...")
    
    # 🔥 drop_pending_updates=True se purane conflicts clear ho jaate hain
    app.run_polling(
        drop_pending_updates=True,   # ye add karo
        allowed_updates=Update.ALL_TYPES
    )

if __name__ == "__main__":
    main()
