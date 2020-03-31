import html
import re
from typing import Optional, List

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery
from telegram import Message, Chat, Update, Bot
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, DispatcherHandlerStop, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, WHITELIST_USERS, TIGER_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import (is_user_admin, bot_admin, user_admin_no_reply, user_admin,
                                                     can_restrict)
from tg_bot.modules.helper_funcs.extraction import extract_text, extract_user_and_text, extract_user
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import split_message
from tg_bot.modules.helper_funcs.string_handling import split_quotes
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import warns_sql as sql

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Current warning filters in this chat:</b>\n"


# Not async
def warn(user: User, chat: Chat, reason: str, message: Message, warner: User = None) -> str:
    if is_user_admin(chat, user.id):
        # message.reply_text("Damn admins, They are too far to be One Punched!")
        return

    if user.id in TIGER_USERS:
        if warner:
            message.reply_text("Tigers cant be warned.")
        else:
            message.reply_text("Tiger triggered an auto warn filter!\n I can't warn tigers but they should avoid abusing this.")
        return

    if user.id in WHITELIST_USERS:
        if warner:
            message.reply_text("Wolf disasters are warn immune.")
        else:
            message.reply_text("Wolf Disaster triggered an auto warn filter!\n I can't warn wolves but they should avoid abusing this.")
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # punch
            chat.unban_member(user.id)
            reply = f"{limit} warnings, *Punches {mention_html(user.id, user.first_name)} with a normal punch!* "

        else:  # ban
            chat.kick_member(user.id)
            reply = f"{limit} warnings, *Punches {mention_html(user.id, user.first_name)} with a Serious Punch* "

        for warn_reason in reasons:
            reply += f"\n - {html.escape(warn_reason)}"

        message.bot.send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = []
        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN_BAN\n"
                      f"<b>Admin:</b> {warner_tag}\n"
                      f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Reason:</b> {reason}\n"
                      f"<b>Counts:</b> <code>{num_warns}/{limit}</code>")

    else:
        keyboard = InlineKeyboardMarkup([{InlineKeyboardButton("Remove warn",
                                                               callback_data="rm_warn({})".format(user.id))}])

        reply = f"{mention_html(user.id, user.first_name)} has {num_warns}/{limit} warnings... watch out!"
        if reason:
            reply += f"\nReason for last warn:\n{html.escape(reason)}"

        log_reason = (f"<b>{html.escape(chat.title)}:</b>\n"
                      f"#WARN\n"
                      f"<b>Admin:</b> {warner_tag}\n"
                      f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
                      f"<b>Reason:</b> {reason}\n"
                      f"<b>Counts:</b> <code>{num_warns}/{limit}</code>")

    try:
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, quote=False)
        else:
            raise
    return log_reason


@run_async
@user_admin_no_reply
@bot_admin
@loggable
def button(bot: Bot, update: Update) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        res = sql.remove_warn(user_id, chat.id)
        if res:
            update.effective_message.edit_text(
                "Warn removed by {}.".format(mention_html(user.id, user.first_name)),
                parse_mode=ParseMode.HTML)
            user_member = chat.get_member(user_id)
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#UNWARN\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}")
        else:
            update.effective_message.edit_text(f"User already has no warns.", parse_mode=ParseMode.HTML)

    return ""


@run_async
@user_admin
@can_restrict
@loggable
def warn_user(bot: Bot, update: Update, args: List[str]) -> str:
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    warner: Optional[User] = update.effective_user

    user_id, reason = extract_user_and_text(message, args)

    if user_id:
        if message.reply_to_message and message.reply_to_message.from_user.id == user_id:
            return warn(message.reply_to_message.from_user, chat, reason, message.reply_to_message, warner)
        else:
            return warn(chat.get_member(user_id).user, chat, reason, message, warner)
    else:
        message.reply_text("That looks like an invalid User ID to me.")
    return ""


@run_async
@user_admin
@bot_admin
@loggable
def reset_warns(bot: Bot, update: Update, args: List[str]) -> str:
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user

    user_id = extract_user(message, args)

    if user_id:
        sql.reset_warns(user_id, chat.id)
        message.reply_text("Warns have been reset!")
        warned = chat.get_member(user_id).user
        return (f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RESETWARNS\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(warned.id, warned.first_name)}")
    else:
        message.reply_text("No user has been designated!")
    return ""


@run_async
def warns(bot: Bot, update: Update, args: List[str]):
    message: Optional[Message] = update.effective_message
    chat: Optional[Chat] = update.effective_chat
    user_id = extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn = sql.get_warn_setting(chat.id)

        if reasons:
            text = f"This user has {num_warns}/{limit} warns, for the following reasons:"
            for reason in reasons:
                text += f"\n - {reason}"

            msgs = split_message(text)
            for msg in msgs:
                update.effective_message.reply_text(msg)
        else:
            update.effective_message.reply_text(f"User has {num_warns}/{limit} warns, but no reasons for any of them.")
    else:
        update.effective_message.reply_text("This user doesn't have any warns!")


# Dispatcher handler stop - do not async
@user_admin
def add_warn_filter(bot: Bot, update: Update):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) >= 2:
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()
        content = extracted[1]

    else:
        return

    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(WARN_HANDLER_GROUP, []):
        if handler.filters == (keyword, chat.id):
            dispatcher.remove_handler(handler, WARN_HANDLER_GROUP)

    sql.add_warn_filter(chat.id, keyword, content)

    update.effective_message.reply_text(f"Warn handler added for '{keyword}'!")
    raise DispatcherHandlerStop


@user_admin
def remove_warn_filter(bot: Bot, update: Update):
    chat: Optional[Chat] = update.effective_chat
    msg: Optional[Message] = update.effective_message

    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        msg.reply_text("No warning filters are active here!")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            msg.reply_text("Okay, I'll stop warning people for that.")
            raise DispatcherHandlerStop

    msg.reply_text("That's not a current warning filter - run /warnlist for all active warning filters.")


@run_async
def list_warn_filters(bot: Bot, update: Update):
    chat: Optional[Chat] = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        update.effective_message.reply_text("No warning filters are active here!")
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if not filter_list == CURRENT_WARNING_FILTER_STRING:
        update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@run_async
@loggable
def reply_filter(bot: Bot, update: Update) -> str:
    chat: Optional[Chat] = update.effective_chat
    message: Optional[Message] = update.effective_message

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            user: Optional[User] = update.effective_user
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return warn(user, chat, warn_filter.reply, message)
    return ""


@run_async
@user_admin
@loggable
def set_warn_limit(bot: Bot, update: Update, args: List[str]) -> str:
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                msg.reply_text("The minimum warn limit is 3!")
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                msg.reply_text("Updated the warn limit to {}".format(args[0]))
                return (f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#SET_WARN_LIMIT\n"
                        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                        f"Set the warn limit to <code>{args[0]}</code>")
        else:
            msg.reply_text("Give me a number as an arg!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)

        msg.reply_text("The current warn limit is {}".format(limit))
    return ""


@run_async
@user_admin
def set_warn_strength(bot: Bot, update: Update, args: List[str]):
    chat: Optional[Chat] = update.effective_chat
    user: Optional[User] = update.effective_user
    msg: Optional[Message] = update.effective_message

    if args:
        if args[0].lower() in ("on", "yes"):
            sql.set_warn_strength(chat.id, False)
            msg.reply_text("Too many warns will now result in a Ban!")
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Has enabled strong warns. Users will be seriously punched.(banned)")

        elif args[0].lower() in ("off", "no"):
            sql.set_warn_strength(chat.id, True)
            msg.reply_text("Too many warns will now result in a normal punch! Users will be able to join again after.")
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Has disabled strong punches. I will use normal punch on users.")

        else:
            msg.reply_text("I only understand on/yes/no/off!")
    else:
        limit, soft_warn = sql.get_warn_setting(chat.id)
        if soft_warn:
            msg.reply_text("Warns are currently set to *punch* users when they exceed the limits.",
                           parse_mode=ParseMode.MARKDOWN)
        else:
            msg.reply_text("Warns are currently set to *Ban* users when they exceed the limits.",
                           parse_mode=ParseMode.MARKDOWN)
    return ""


def __stats__():
    return (f"{sql.num_warns()} overall warns, across {sql.num_warn_chats()} chats.\n"
            f"{sql.num_warn_filters()} warn filters, across {sql.num_warn_filter_chats()} chats.")


def __import_data__(chat_id, data):
    for user_id, count in data.get('warns', {}).items():
        for x in range(int(count)):
            sql.warn_user(user_id, chat_id)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (f"This chat has `{num_warn_filters}` warn filters. "
            f"It takes `{limit}` warns before the user gets *{'kicked' if soft_warn else 'banned'}*.")


__help__ = """
 - /warns <userhandle>: get a user's number, and reason, of warns.
 - /warnlist: list of all current warning filters

*Admins only:*
 - /warn <userhandle>: warn a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
 - /resetwarn <userhandle>: reset the warns for a user. Can also be used as a reply.
 - /addwarn <keyword> <reply message>: set a warning filter on a certain keyword. If you want your keyword to \
be a sentence, encompass it with quotes, as such: `/addwarn "very angry" This is an angry user`. 
 - /nowarn <keyword>: stop a warning filter
 - /warnlimit <num>: set the warning limit
 - /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just punch.
"""

__mod_name__ = "Warnings"

WARN_HANDLER = CommandHandler("warn", warn_user, pass_args=True, filters=Filters.group)
RESET_WARN_HANDLER = CommandHandler(["resetwarn", "resetwarns"], reset_warns, pass_args=True, filters=Filters.group)
CALLBACK_QUERY_HANDLER = CallbackQueryHandler(button, pattern=r"rm_warn")
MYWARNS_HANDLER = DisableAbleCommandHandler("warns", warns, pass_args=True, filters=Filters.group)
ADD_WARN_HANDLER = CommandHandler("addwarn", add_warn_filter, filters=Filters.group)
RM_WARN_HANDLER = CommandHandler(["nowarn", "stopwarn"], remove_warn_filter, filters=Filters.group)
LIST_WARN_HANDLER = DisableAbleCommandHandler(["warnlist", "warnfilters"], list_warn_filters, filters=Filters.group,
                                              admin_ok=True)
WARN_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & Filters.group, reply_filter)
WARN_LIMIT_HANDLER = CommandHandler("warnlimit", set_warn_limit, pass_args=True, filters=Filters.group)
WARN_STRENGTH_HANDLER = CommandHandler("strongwarn", set_warn_strength, pass_args=True, filters=Filters.group)

dispatcher.add_handler(WARN_HANDLER)
dispatcher.add_handler(CALLBACK_QUERY_HANDLER)
dispatcher.add_handler(RESET_WARN_HANDLER)
dispatcher.add_handler(MYWARNS_HANDLER)
dispatcher.add_handler(ADD_WARN_HANDLER)
dispatcher.add_handler(RM_WARN_HANDLER)
dispatcher.add_handler(LIST_WARN_HANDLER)
dispatcher.add_handler(WARN_LIMIT_HANDLER)
dispatcher.add_handler(WARN_STRENGTH_HANDLER)
dispatcher.add_handler(WARN_FILTER_HANDLER, WARN_HANDLER_GROUP)
