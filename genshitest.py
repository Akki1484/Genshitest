from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pymongo import MongoClient
from decouple import config
import requests

# Load the connection string from the .env file
MONGODB_URI = config("mongodb+srv://jinwoo210606:<uvnQf4Mw1irCo6z2>@cluster0.beb11.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)
db = client.genshin_bot  # Database name
users_collection = db.users  # Collection name

# Fetch daily note data from Hoyolab API
def fetch_daily_note(ltoken, ltuid):
    url = "https://bbs-api-os.hoyolab.com/game_record/genshin/api/dailyNote"
    headers = {
        "Cookie": f"ltoken={ltoken}; ltuid={ltuid}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()  # Returns daily note data as a dictionary
    else:
        return None

# Command to start the bot and save user data
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if the user already exists in the database
    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data:
        # Add new user to the database
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "resin": 0,  # Example: Resin tracking
            "characters": []  # Example: List of favorite characters
        })
        update.message.reply_text("Welcome to the Genshin Impact Bot! Use /login to link your Hoyolab account.")
    else:
        update.message.reply_text("Welcome back! Use /login to link your Hoyolab account.")

# Command to log in with Hoyolab token
def login(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    try:
        ltoken = context.args[0]  # Get ltoken from command
        ltuid = context.args[1]   # Get ltuid from command

        # Save tokens to the database
        users_collection.update_one({"user_id": user_id}, {"$set": {"ltoken": ltoken, "ltuid": ltuid}}, upsert=True)
        update.message.reply_text("Your Hoyolab account has been linked!")
    except IndexError:
        update.message.reply_text("Usage: /login <ltoken> <ltuid>")

# Command to log out
def logout(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    users_collection.update_one({"user_id": user_id}, {"$unset": {"ltoken": "", "ltuid": ""}})
    update.message.reply_text("Your Hoyolab account has been unlinked.")

# Command to display daily note data
def show_daily_note(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    if not user_data or "ltoken" not in user_data or "ltuid" not in user_data:
        update.message.reply_text("You are not logged in. Use /login to link your Hoyolab account.")
        return

    ltoken = user_data["ltoken"]
    ltuid = user_data["ltuid"]
    daily_note = fetch_daily_note(ltoken, ltuid)
    if not daily_note:
        update.message.reply_text("Failed to fetch data. Please check your login token.")
        return

    # Extract data from the response
    resin = daily_note.get("current_resin", "Unknown")
    max_resin = daily_note.get("max_resin", "Unknown")
    commissions = daily_note.get("finished_task_num", "Unknown")
    max_commissions = daily_note.get("total_task_num", "Unknown")
    expeditions = daily_note.get("current_expedition_num", "Unknown")
    max_expeditions = daily_note.get("max_expedition_num", "Unknown")

    # Format the message
    message = (
        f"Resin: {resin}/{max_resin}\n"
        f"Daily Commissions: {commissions}/{max_commissions}\n"
        f"Expeditions: {expeditions}/{max_expeditions}"
    )
    update.message.reply_text(message)

def main() -> None:
    # Replace 'YOUR_API_TOKEN' with your bot's API token
    updater = Updater(config("7605487283:AAEqVUtr6kxJ-12mW36iEf9hk97vH1apVkQ"))

    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("login", login))
    dispatcher.add_handler(CommandHandler("logout", logout))
    dispatcher.add_handler(CommandHandler("daily", show_daily_note))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()