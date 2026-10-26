# Python ka official image use kar rahe hain
FROM python:3.11-slim

# Server ke andar ek folder bana rahe hain
WORKDIR /app

# Apne saare files (bot.py, requirements.txt) server ke andar copy kar rahe hain
COPY . /app

# Requirements install kar rahe hain (Flask aur Telegram library)
RUN pip install --no-cache-dir -r requirements.txt

# Bot is port par chalega (Flask ke liye zaroori hai)
EXPOSE 8080

# Bot.py ko run karne ka command
CMD ["python", "bot.py"]
