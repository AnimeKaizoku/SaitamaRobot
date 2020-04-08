import html
from typing import List

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest
from telegram.ext import MessageHandler, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, WHITELIST_USERS, TIGER_USERS
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict, connection_status
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    log_message = ""

    if not user:  # ignore channels
        return log_message

    # ignore admins and whitelists
    if (is_user_admin(chat, user.id) 
            or user.id in WHITELIST_USERS
            or user.id in TIGER_USERS):
        sql.update_flood(chat.id, None)
        return log_message

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return log_message

    try:
        bot.restrict_chat_member(chat.id, user.id, can_send_messages=False)
        msg.reply_text(f"*mutes {mention_html(user.id, user.first_name)} permanently*\nStop flooding the group!", parse_mode=ParseMode.HTML)
        log_message = (f"<b>{html.escape(chat.title)}:</b>\n"
                       f"#MUTED\n"
                       f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
                       f"Flooded the group.\nMuted until an admin unmutes")

        return log_message

    except BadRequest:
        msg.reply_text("I can't kick people here, give me permissions first! Until then, I'll disable antiflood.")
        sql.set_flood(chat.id, 0)
        log_message = ("<b>{chat.title}:</b>\n"
                       "#INFO\n"
                       "Don't have kick permissions, so automatically disabled antiflood.")

        return log_message


@run_async
@connection_status
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""

    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        chat_name = ""
    else:
        chat_name = f" in <b>{update_chat_title}</b>"

    if len(args) >= 1:

        val = args[0].lower()

        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("Antiflood has been disabled{}.".format(chat_name), parse_mode=ParseMode.HTML)

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("Antiflood has been disabled{}.".format(chat_name), parse_mode=ParseMode.HTML)
                log_message = (f"<b>{html.escape(chat.title)}:</b>\n"
                               f"#SETFLOOD\n"
                               f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
                               f"Disabled antiflood.")

                return log_message
            elif amount < 3:
                message.reply_text("Antiflood has to be either 0 (disabled), or a number bigger than 3!")
                return log_message

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("Antiflood has been updated and set to {}{}".format(amount, chat_name),
                                   parse_mode=ParseMode.HTML)
                log_message = (f"<b>{html.escape(chat.title)}:</b>\n"
                               f"#SETFLOOD\n"
                               f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
                               f"Set antiflood to <code>{amount}</code>.")

                return log_message
        else:
            message.reply_text("Unrecognised argument - please use a number, 'off', or 'no'.")

    return log_message


@run_async
@connection_status
def flood(bot: Bot, update: Update):
    chat = update.effective_chat
    update_chat_title = chat.title
    message_chat_title = update.effective_message.chat.title

    if update_chat_title == message_chat_title:
        chat_name = ""
    else:
        chat_name = f" in <b>{update_chat_title}</b>"

    limit = sql.get_flood_limit(chat.id)

    if limit == 0:
        update.effective_message.reply_text(f"I'm not currently enforcing flood control{chat_name}!",
                                            parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(f"I'm currently muting users if they send "
                                            f"more than {limit} consecutive messages{chat_name}.",
                                            parse_mode=ParseMode.HTML)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "*Not* currently enforcing flood control."
    else:
        return "Antiflood is set to `{}` messages.".format(limit)


__help__ = """
 - /flood: Get the current flood control setting

*Admin only:*
 - /setflood <int/'no'/'off'>: enables or disables flood control
 Example: /setflood 10
 This will mute users if they send more than 10 messages in a row, bots are ignored.
"""

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True)
FLOOD_HANDLER = CommandHandler("flood", flood)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__mod_name__ = "AntiFlood"
__handlers__ = [(FLOOD_BAN_HANDLER, FLOOD_GROUP), SET_FLOOD_HANDLER, FLOOD_HANDLER]
