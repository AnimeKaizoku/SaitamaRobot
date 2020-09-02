import html
import re
import requests

from SaitamaRobot import (DEV_USERS, OWNER_ID, SUDO_USERS, SUPPORT_USERS,
                          TIGER_USERS, WHITELIST_USERS, dispatcher, sw)
from SaitamaRobot.__main__ import STATS, TOKEN, USER_INFO
import SaitamaRobot.modules.sql.userinfo_sql as sql
from SaitamaRobot import DEV_USERS, SUDO_USERS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.extraction import extract_user
from SaitamaRobot.modules.sql.afk_sql import is_afk
from SaitamaRobot.modules.sql.users_sql import get_user_num_chats
from SaitamaRobot.modules.helper_funcs.chat_status import sudo_plus, user_admin
from SaitamaRobot.modules.helper_funcs.extraction import extract_user

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import MAX_MESSAGE_LENGTH, ParseMode, Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters
from telegram.utils.helpers import mention_html


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return f"<b>About user:</b>\n{me}\n<b>What others say:</b>\n{bio}"
    elif bio:
        return f"<b>What others say:</b>\n{bio}\n"
    elif me:
        return f"<b>About user:</b>\n{me}"
    else:
        return ""

def make_bar(per):
     msg = ""
     if per <= 10000:
        return "■■■■■■■■■■"
     for x in range(int(round(per/10, 0))): msg += '■'
     for x in range(10-len(msg)): msg += '□'
     return msg

@run_async
def get_id(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    user_id = extract_user(msg, args)

    if user_id:

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            msg.reply_text(
                f"The original sender, {html.escape(user2.first_name)},"
                f" has an ID of <code>{user2.id}</code>.\n"
                f"The forwarder, {html.escape(user1.first_name)},"
                f" has an ID of <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:

            user = bot.get_chat(user_id)
            msg.reply_text(
                f"{html.escape(user.first_name)}'s id is <code>{user.id}</code>.",
                parse_mode=ParseMode.HTML)

    else:

        if chat.type == "private":
            msg.reply_text(
                f"Your id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)

        else:
            msg.reply_text(
                f"This group's id is <code>{chat.id}</code>.",
                parse_mode=ParseMode.HTML)


@run_async
def gifid(update: Update, context: CallbackContext):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


@run_async
def info(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@") and
         not args[0].isdigit() and
         not message.parse_entities([MessageEntity.TEXT_MENTION]))):
        message.reply_text("I can't extract a user from this.")
        return

    else:
        return

    text = (f"<b>Characteristics:</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"First Name: {html.escape(user.first_name)}")

    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"

    text += f"\nPermalink: {mention_html(user.id, 'link')}"
    chat_count = get_user_num_chats(user.id)
    if chat.type != "private":
       _stext = "\nStatus: {}"

       afk_st = is_afk(user.id)
       if afk_st:
          text += _stext.format("Sleeping")
       else:
          status = status = bot.get_chat_member(chat.id, user.id).status
          if status:
              if status in {"left", "kicked"}:
                  text += _stext.format("Absent")
              elif status == "member":
                  text += _stext.format("Present")
              elif status in {"administrator", "creator"}:
                  text += _stext.format("Admin")
    hp = (chat_count+1)*50
    percentage = (hp/10000)*100
    text += f"\n<b>Health</b>: {hp}/10000\n<code>{make_bar(percentage)}</code> {percentage}%"
    try:
        spamwtc = sw.get_ban(int(user.id))
        if spamwtc:
            text += "\n\n<b>This person is Spamwatched!</b>"
            text += f"\nReason: <pre>{spamwtc.reason}</pre>"
            text += "\nAppeal at @SpamWatchSupport"
        else:
            pass
    except:
        pass  # don't crash if api is down somehow...

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\nThe Disaster level of this person is 'God'."
        disaster_level_present = True
    elif user.id in DEV_USERS:
        text += "\n\nThis member is one of 'Hero Association'."
        disaster_level_present = True
    elif user.id in SUDO_USERS:
        text += "\n\nThe Disaster level of this person is 'Dragon'."
        disaster_level_present = True
    elif user.id in SUPPORT_USERS:
        text += "\n\nThe Disaster level of this person is 'Demon'."
        disaster_level_present = True
    elif user.id in TIGER_USERS:
        text += "\n\nThe Disaster level of this person is 'Tiger'."
        disaster_level_present = True
    elif user.id in WHITELIST_USERS:
        text += "\n\nThe Disaster level of this person is 'Wolf'."
        disaster_level_present = True

    if disaster_level_present:
        text += ' [<a href="https://t.me/{}?start=disasters">?</a>]'.format(
            bot.username)

    try:
        user_member = chat.get_member(user.id)
        if user_member.status == 'administrator':
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result['custom_title']
                text += f"\n\nThis user holds the title <b>{custom_title}</b> here."
    except BadRequest:
        pass

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(
        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
def about_me(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_me_info(user.id)

    if info:
        update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(
            f"{username} hasn't set an info message about themselves yet!")
    else:
        update.effective_message.reply_text(
            "You haven't set an info message about yourself yet!")


@run_async
def set_about_me(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id
    bot = context.bot
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id == bot.id and (user_id in SUDO_USERS or
                                       user_id in DEV_USERS):
            user_id = repl_user_id

    text = message.text
    info = text.split(None, 1)

    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id == bot.id:
                message.reply_text("Updated my info!")
            else:
                message.reply_text("Updated your info!")
        else:
            message.reply_text(
                "The info needs to be under {} characters! You have {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])))

@run_async
@sudo_plus
def stats(update: Update, context: CallbackContext):
    stats = "Current stats:\n" + "\n".join([mod.__stats__() for mod in STATS])
    result = re.sub(r'(\d+)', r'<code>\1</code>', stats)
    update.effective_message.reply_text(result, parse_mode=ParseMode.HTML)


@run_async
def about_bio(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = user.first_name
        update.effective_message.reply_text(
            f"{username} hasn't had a message set about themselves yet!")
    else:
        update.effective_message.reply_text(
            "You haven't had a bio set about yourself yet!")


@run_async
def set_about_bio(update: Update, context: CallbackContext):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            message.reply_text(
                "Ha, you can't set your own bio! You're at the mercy of others here..."
            )
            return

        if user_id == bot.id and sender_id not in SUDO_USERS and sender_id not in DEV_USERS:
            message.reply_text(
                "Erm... yeah, I only trust sudo users or developers to set my bio."
            )
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                message.reply_text("Updated {}'s bio!".format(
                    repl_message.from_user.first_name))
            else:
                message.reply_text(
                    "A bio needs to be under {} characters! You tried to set {}."
                    .format(MAX_MESSAGE_LENGTH // 4, len(bio[1])))
    else:
        message.reply_text("Reply to someone's message to set their bio!")



__help__ = """
*ID:*
 • `/id`*:* get the current group id. If used by replying to a message, gets that user's id.
 • `/gifid`*:* reply to a gif to me to tell you its file ID.

*Self addded information:* 
 • `/setme <text>`*:* will set your info
 • `/me`*:* will get your or another user's info.
Examples:
 `/setme I am a wolf.`
 `/me @username(defaults to yours if no user specified)`

*Information others add on you:* 
 • `/bio`*:* will get your or another user's bio. This cannot be set by yourself.
• `/setbio <text>`*:* while replying, will save another user's bio 
Examples:
 `/bio @username(defaults to yours if not specified).`
 `/setbio This user is a wolf` (reply to the user)

*Overall Information about you:*
 • `/info`*:* get information about a user. 
"""

SET_BIO_HANDLER = DisableAbleCommandHandler("setbio", set_about_bio)
GET_BIO_HANDLER = DisableAbleCommandHandler("bio", about_bio)

STATS_HANDLER = CommandHandler("stats", stats)
ID_HANDLER = DisableAbleCommandHandler("id", get_id)
GIFID_HANDLER = DisableAbleCommandHandler("gifid", gifid)
INFO_HANDLER = DisableAbleCommandHandler(["info"], info)

SET_ABOUT_HANDLER = DisableAbleCommandHandler("setme", set_about_me)
GET_ABOUT_HANDLER = DisableAbleCommandHandler("me", about_me)

dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(GIFID_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
dispatcher.add_handler(SET_ABOUT_HANDLER)
dispatcher.add_handler(GET_ABOUT_HANDLER)

__mod_name__ = "Info"
__command_list__ = ["setbio", "bio", "setme", "me", "info"]
__handlers__ = [
    ID_HANDLER, GIFID_HANDLER, INFO_HANDLER, SET_BIO_HANDLER, GET_BIO_HANDLER, SET_ABOUT_HANDLER, GET_ABOUT_HANDLER, STATS_HANDLER
]
