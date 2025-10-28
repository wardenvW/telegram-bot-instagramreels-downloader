import telebot
import os
import logging
import instaloader
import json
import sys
from datetime import datetime

from db.database import get_all_users, block_user, unblock_user, find_user, add_admin, delete_admin
from db.initialization import init_database
from validators import get_shortcode_from_url
from tempfile import TemporaryDirectory
from pathlib import Path
from decorators import user, admin, s_admin
from dotenv import load_dotenv

def setup_logging():

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    return logger

logger = setup_logging()
telebot.logger.setLevel(logging.WARNING)

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
if not API_TOKEN:
    logger.error("API_TOKEN not found in environment variables!")
    sys.exit(1)

bot = telebot.TeleBot(API_TOKEN)
logger.info("Bot initialized")

try:
    init_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    sys.exit(1)

# | USER COMMANDS |

@bot.message_handler(commands=['start'])
@user
def start_message(message: telebot.types.Message):
    logger.info(f"User {message.from_user.id} ({message.from_user.username}) started the bot")
    bot.send_message(message.chat.id, "Hello, it's gamma bot\n/reels - to download an instagram reels")

@bot.message_handler(commands=['reels'])
@user
def send_url_message_request(message: telebot.types.Message):
    logger.info(f"User {message.from_user.id} requested reels download")
    msg = bot.reply_to(message, "Enter URL")
    bot.register_next_step_handler(msg, download_reels)

def download_reels(message: telebot.types.Message):
    user_id = message.from_user.id
    url = message.text
    logger.info(f"User {user_id} provided URL: {url}")

    shortcode = get_shortcode_from_url(url)
    if not shortcode:
        logger.warning(f"User {user_id} provided invalid URL: {url}")
        msg = bot.reply_to(message, 'Its not valid url, try again')
        bot.register_next_step_handler(msg, download_reels)
        return
    
    
    
    logger.info(f"User {user_id} downloading reels with shortcode: {shortcode}")
    
    with TemporaryDirectory() as d:
        target = Path(d)
        L = instaloader.Instaloader()

        L.download_video_thumbnails = False  
        L.post_metadata_txt_pattern = ""
        L.save_metadata = False
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode=shortcode) 
            L.download_post(post, target=target)
        
            video_found = False
            for file in target.iterdir():
                if file.suffix == ".mp4":
                    with open(file, 'rb') as video:
                        file_size = os.path.getsize(file)
                        logger.info(f"User {user_id} successfully downloaded reels, file size: {file_size} bytes")
                        bot.send_video(message.chat.id, video)
                        video_found = True
                        break
            
            if not video_found:
                logger.error(f"No MP4 file found for user {user_id}, shortcode: {shortcode}")
                bot.send_message(message.chat.id, "An error occurred, while tried to download reels")
                
        except instaloader.exceptions.BadResponseException as e:
            logger.warning(f"User {user_id} tried to download private reels: {e}")
            bot.send_message(message.chat.id, "It's private reels, i cant download it")

# | ADMIN COMMANDS |

#get logs
@bot.message_handler(commands=['logs'])
@admin
def send_logs(message: telebot.types.Message):
    logger.info(f"Admin {message.from_user.id} requested logs")
    try:
        if os.path.exists('bot.log'):
            with open('bot.log', 'rb') as log_file:
                bot.send_document(message.chat.id, log_file, caption="logs")
                logger.info(f"Logs sent to admin {message.from_user.id}")
        else:
            bot.send_message(message.chat.id, "No logs found")
            logger.warning(f"No log file found for admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error sending logs to admin {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "Error retrieving logs")

#get all users info
@bot.message_handler(commands=['all'])
@s_admin
def send_users_data(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} requested all users data")
    try:
        users_tuple = get_all_users()
        json_data = {"users": [{'id': user[0], 'role': user[1]} for user in users_tuple]}
        json_file_name = "users.json"

        with open(json_file_name, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)
        with open(json_file_name, 'rb') as json_file:
            bot.send_document(message.chat.id, json_file)
        logger.info(f"Sent {len(users_tuple)} users to super admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error getting users data for super admin {message.from_user.id}: {e}")
        bot.send_message(message.chat.id, "Error retrieving users data")

#find user(get information)
@bot.message_handler(commands=['find'])
@s_admin
def get_user_info(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} initiated user search")
    bot.send_message(message.chat.id, "Enter a user's id you want to find")
    bot.register_next_step_handler(message, process_find)

def process_find(message: telebot.types.Message):
    admin_id = message.from_user.id
    search_id = message.text

    if search_id == 'cancel':
        logger.info(f"Super admin {admin_id} canceled user search")
        return bot.send_message(message.chat.id, "canceled")

    if not search_id.isdigit():
        logger.warning(f"Super admin {admin_id} provided invalid user ID: {search_id}")
        bot.reply_to(message, "Not valid id (only numbers required)\n(cancel - to exit)")
        return bot.register_next_step_handler(message, process_find)

    user_id = int(search_id)
    logger.info(f"Super admin {admin_id} searching for user {user_id}")
    
    result = find_user(user_id)
    if result:
        logger.info(f"Super admin {admin_id} found user {user_id} with role {result[1]}")
        bot.send_message(message.chat.id, f"User found\nid: {result[0]}\nrole: {result[1]}")
    else:
        logger.info(f"Super admin {admin_id} user {user_id} not found")
        bot.send_message(message.chat.id, "❌ User not found")


#block user
@bot.message_handler(commands=['block'])
@s_admin
def block_user_cmd(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} initiated user block")
    bot.send_message(message.chat.id, "Enter a user's id you want to block")
    bot.register_next_step_handler(message, process_block)

def process_block(message: telebot.types.Message):
    admin_id = message.from_user.id
    block_id = message.text

    if block_id == 'cancel':
        logger.info(f"Super admin {admin_id} canceled block operation")
        return bot.send_message(message.chat.id, "canceled")

    if not block_id.isdigit():
        logger.warning(f"Super admin {admin_id} provided invalid user ID for block: {block_id}")
        bot.reply_to(message, "Not valid id (only numbers required)\n(cancel - to exit)")
        return bot.register_next_step_handler(message, process_block)

    user_id = int(block_id)
    logger.info(f"Super admin {admin_id} blocking user {user_id}")
    
    result = block_user(user_id)
    if result:
        logger.warning(f"Super admin {admin_id} blocked user {user_id}")
        bot.send_message(message.chat.id, "✅ User blocked")
    else:
        logger.info(f"Super admin {admin_id} failed to block user {user_id} (not found)")
        bot.send_message(message.chat.id, "❌ User not found")


#unblock user
@bot.message_handler(commands=['unblock'])
@s_admin
def unblock_user_command(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} initiated user unblock")
    bot.send_message(message.chat.id, "Enter a user's id you want to unblock")
    bot.register_next_step_handler(message, process_unblock)

def process_unblock(message: telebot.types.Message):
    admin_id = message.from_user.id
    unblock_id = message.text

    if unblock_id == 'cancel':
        logger.info(f"Super admin {admin_id} canceled unblock operation")
        return bot.send_message(message.chat.id, "canceled")
    
    if not unblock_id.isdigit():
        logger.warning(f"Super admin {admin_id} provided invalid user ID for unblock: {unblock_id}")
        bot.reply_to(message, "Not valid id (only numbers required)\n(cancel - to exit)")
        return bot.register_next_step_handler(message, process_unblock)
    
    user_id = int(unblock_id)
    logger.info(f"Super admin {admin_id} unblocking user {user_id}")
    
    result = unblock_user(user_id)
    if result:
        logger.info(f"Super admin {admin_id} unblocked user {user_id}")
        bot.send_message(message.chat.id, "✅ User unblocked")
    else:
        logger.info(f"Super admin {admin_id} failed to unblock user {user_id} (not found)")
        bot.send_message(message.chat.id, "❌ User not found")


#add admin 
@bot.message_handler(commands=['add_admin'])
@s_admin
def add_admin_cmd(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} initiated add admin")
    bot.send_message(message.chat.id, "Enter a user's id you want to make admin")
    bot.register_next_step_handler(message, process_add_admin)

def process_add_admin(message: telebot.types.Message):
    admin_id = message.from_user.id
    new_admin_id = message.text

    if new_admin_id == 'cancel':
        logger.info(f"Super admin {admin_id} canceled add admin operation")
        return bot.send_message(message.chat.id, "canceled")
    
    if not new_admin_id.isdigit():
        logger.warning(f"Super admin {admin_id} provided invalid user ID for admin promotion: {new_admin_id}")
        bot.reply_to(message, "Not valid id (only numbers required)\n(cancel - to exit)")
        return bot.register_next_step_handler(message, process_add_admin)
    
    user_id = int(new_admin_id)
    logger.info(f"Super admin {admin_id} promoting user {user_id} to admin")
    
    result = add_admin(user_id)
    if result:
        logger.warning(f"Super admin {admin_id} promoted user {user_id} to admin")
        bot.send_message(message.chat.id, "✅ Admin added")
    else:
        logger.info(f"Super admin {admin_id} failed to promote user {user_id} to admin (not found)")
        bot.send_message(message.chat.id, "❌ User not found")


#delete admin
@bot.message_handler(commands=['delete_admin'])
@s_admin
def delete_admin_cmd(message: telebot.types.Message):
    logger.info(f"Super admin {message.from_user.id} initiated delete admin")
    bot.send_message(message.chat.id, "Enter a user's id you want to remove from admins")
    bot.register_next_step_handler(message, process_delete_admin)

def process_delete_admin(message: telebot.types.Message):
    admin_id = message.from_user.id
    remove_admin_id = message.text

    if remove_admin_id == 'cancel':
        logger.info(f"Super admin {admin_id} canceled delete admin operation")
        return bot.send_message(message.chat.id, "canceled")
    
    if not remove_admin_id.isdigit():
        logger.warning(f"Super admin {admin_id} provided invalid user ID for admin removal: {remove_admin_id}")
        bot.reply_to(message, "Not valid id (only numbers required)\n(cancel - to exit)")
        return bot.register_next_step_handler(message, process_delete_admin)
    
    user_id = int(remove_admin_id)
    logger.info(f"Super admin {admin_id} removing admin rights from user {user_id}")
    
    result = delete_admin(user_id)
    if result:
        logger.warning(f"Super admin {admin_id} removed admin rights from user {user_id}")
        bot.send_message(message.chat.id, "✅ Admin deleted")
    else:
        logger.info(f"Super admin {admin_id} failed to remove admin rights from user {user_id} (not found or not admin)")
        bot.send_message(message.chat.id, "❌ Admin not found")


if __name__ == "__main__":
    logger.info("Starting bot...")
    try:
        bot.enable_save_next_step_handlers(delay=1)
        bot.load_next_step_handlers()
        logger.info("Bot handlers loaded, starting polling...")
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
        sys.exit(1)