import telebot
import logging
from db.database import get_user_role

logging.getLogger().setLevel(logging.INFO)

ROLES = {
    'blocked': 0,
    'user': 1,
    'admin': 2,
    's_admin': 3
}




def user(func):
    def wrapper(message: telebot.types.Message, *args, **kwargs):
        user_id = message.from_user.id
        user_role = get_user_role(user_id)


        if ROLES[user_role] >= ROLES['user']:
            return func(message, *args, **kwargs)
        
        logging.info(f"user({user_id}) cannot get access (reason-blocked)")
        return
    return wrapper

def admin(func):
    def wrapper(message: telebot.types.Message, *args, **kwargs):  
        user_id = message.from_user.id
        user_role = get_user_role(user_id)

        if ROLES[user_role] >= ROLES['admin']:
            return func(message, *args, **kwargs)
        
        logging.info(f"admin({user_id}) cannot get access (reason-blocked)")
        return
    return wrapper

def s_admin(func):
    def wrapper(message: telebot.types.Message, *args, **kwargs):
        user_id = message.from_user.id
        user_role = get_user_role(user_id)

        if ROLES[user_role] >= ROLES['s_admin']:
            return func(message, *args, **kwargs)
        return
    return wrapper


