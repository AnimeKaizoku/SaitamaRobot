from time import sleep

from telegram import Update, Bot
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import dev_plus

import tg_bot.modules.sql.users_sql as user_sql
import tg_bot.modules.sql.global_bans_sql as gban_sql

@run_async
@dev_plus
def dbcleanup(bot: Bot, update: Update):

    msg = update.effective_message
    msg.reply_text("Cleaning up chats ...")

    chats = user_sql.get_all_chats()
    kicked_chats = 0

    for chat in chats:
        id = chat.chat_id
        sleep(0.1) # Reduce floodwait
        try:
            bot.get_chat(id, timeout=60)
        except (BadRequest, Unauthorized):
            kicked_chats += 1
            user_sql.rem_chat(id)

    if kicked_chats >= 1:
        msg.reply_text("Done! {} chats were removed from the database!".format(kicked_chats))
    else:
        msg.reply_text("No chats had to be removed from the database!")

    msg.reply_text("Cleaning up gbans ...")

    banned = gban_sql.get_gban_list()
    ungbanned_users = 0

    for user in banned:
        user_id = user["user_id"]
        sleep(0.1)
        try:
            bot.get_chat(user_id)
        except BadRequest:
            ungbanned_users += 1
            gban_sql.ungban_user(user_id)

    if ungbanned_users >= 1:
        msg.reply_text("Done! {} users were removed from the database!".format(ungbanned_users))
    else:
        msg.reply_text("No users had to be removed from the database!")


DB_CLEANUP_HANDLER = CommandHandler("dbcleanup", dbcleanup)

dispatcher.add_handler(DB_CLEANUP_HANDLER)

__mod_name__ = "DB Cleanup"
