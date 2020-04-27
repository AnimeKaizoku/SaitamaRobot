import os
from time import sleep
from typing import List

from telegram import Update, Message, Bot
from telegram.error import BadRequest, Unauthorized, RetryAfter
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async

from tg_bot import dispatcher, OWNER_ID
from tg_bot.modules.sql.users_sql import get_user_com_chats
from tg_bot.modules.helper_funcs.extraction import extract_user


@run_async
def get_user_common_chats(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    user = extract_user(msg, args)
    if not user:
        msg.reply_text("I share no common chats with the void.")
        return
    common_list = get_user_com_chats(user)
    if not common_list:
        msg.reply_text("No common chats with this user!")
        return
    name = bot.get_chat(user).first_name
    text = f"<b>Common chats with {name}</b>\n"
    for chat in common_list:
        try:
            chat_name = bot.get_chat(chat).title
            sleep(0.3)
            text += f"• <code>{chat_name}</code>\n"
        except BadRequest:
            pass
        except Unauthorized:
            pass
        except RetryAfter as e:
            sleep(e.retry_after)
            
    if len(text) < 4096:
        msg.reply_text(text, parse_mode="HTML")
    else:
        with open("common_chats.txt", 'w') as f:
            f.write(text)
        with open("common_chats.txt", 'rb') as f:
            msg.reply_document(f)
        os.remove("common_chats.txt")
        
COMMON_CHATS_HANDLER = CommandHandler(
    "getchats",
    get_user_common_chats,
    filters=Filters.user(OWNER_ID),
    pass_args=True
    )
    
dispatcher.add_handler(COMMON_CHATS_HANDLER)