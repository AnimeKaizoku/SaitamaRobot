import re
import time
from typing import List

from telegram import Bot, Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, CallbackQueryHandler, run_async

import tg_bot.modules.sql.connection_sql as sql
from tg_bot import dispatcher, SUDO_USERS, DEV_USERS, spamfilters
from tg_bot.modules.helper_funcs import chat_status
from tg_bot.modules.helper_funcs.alternate import send_message

user_admin = chat_status.user_admin

ADMIN_STATUS = ('administrator', 'creator')
MEMBER_STAUS = ('member',)


@user_admin
@run_async
def allow_connections(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(update.effective_message, "Connection has been disabled for this chat")
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(update.effective_message, "Connection has been enabled for this chat")
            else:
                send_message(update.effective_message, "Please enter `yes` or `no`!", parse_mode=ParseMode.MARKDOWN)
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(update.effective_message, "Connections to this group are *Allowed* for members!",
                             parse_mode=ParseMode.MARKDOWN)
            else:
                send_message(update.effective_message, "Connection to this group are *Not Allowed* for members!",
                             parse_mode=ParseMode.MARKDOWN)
    else:
        send_message(update.effective_message, "This command is for group only. Not in PM!")


@run_async
def connection_chat(bot: Bot, update: Update):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    spam = spamfilters(msg.text, msg.from_user.id, update.effective_chat.id)
    if spam is True:
        return

    conn = connected(bot, update, chat, user.id, need_admin=True)

    if conn:
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if msg.chat.type != "private":
            return
        chat_name = chat.title

    if conn:
        message = "You are currently connected with {}.\n".format(chat_name)
    else:
        message = "You are currently not connected in any group.\n"
    send_message(msg, message, parse_mode="markdown")


@run_async
def connect_chat(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    spam = spamfilters(msg.text, msg.from_user.id, chat.id)
    if spam is True:
        return

    if chat.type == 'private':
        if len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = bot.get_chat_member(connect_chat, msg.from_user.id)
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = bot.get_chat_member(connect_chat, msg.from_user.id)
                except BadRequest:
                    send_message(msg, "Invalid Chat ID!")
                    return
            except BadRequest:
                send_message(msg, "Invalid Chat ID!")
                return

            isadmin = getstatusadmin.status in ADMIN_STATUS
            ismember = getstatusadmin.status in MEMBER_STAUS
            isallow = sql.allow_connect_to_chat(connect_chat)

            if isadmin or (isallow and ismember) or (user.id in SUDO_USERS) or (user.id in DEV_USERS):
                connection_status = sql.connect(msg.from_user.id, connect_chat)
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(connected(bot, update, chat, user.id, need_admin=False))
                    chat_name = conn_chat.title
                    send_message(msg, "Successfully connected to *{chat_name}*."
                                      " Use /connection for see current available commands.",
                                 parse_mode=ParseMode.MARKDOWN)
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    send_message(msg, "Connection failed!")
            else:
                send_message(msg, "Connection to this chat is not allowed!")
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(text="❎ Close button", callback_data="connect_close"),
                    InlineKeyboardButton(text="🧹 Clear history", callback_data="connect_clear")
                ]
            else:
                buttons = []
            conn = connected(bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = "You are connected to *{}* (`{}`)".format(connectedchat.title, conn)
                buttons.append(InlineKeyboardButton(text="🔌 Disconnect", callback_data="connect_disconnect"))
            else:
                text = "Write the chat ID or tag to connect!"
            if gethistory:
                text += "\n\n*Connection history:*\n"
                text += "╒═══「 *Info* 」\n"
                text += "│  Sorted: `Newest`\n"
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(gethistory[x]['chat_name'],
                                                                      gethistory[x]['chat_id'], htime)
                    text += "│\n"
                    buttons.append([InlineKeyboardButton(text=gethistory[x]['chat_name'],
                                                         callback_data="connect({})".format(gethistory[x]['chat_id']))])
                text += "╘══「 Total {} Chats 」".format(
                    str(len(gethistory)) + " (max)" if len(gethistory) == 5 else str(len(gethistory)))
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(msg, text, parse_mode="markdown", reply_markup=conn_hist)

    else:
        getstatusadmin = bot.get_chat_member(chat.id, msg.from_user.id)
        isadmin = getstatusadmin.status in ADMIN_STATUS
        ismember = getstatusadmin.status in MEMBER_STAUS
        isallow = sql.allow_connect_to_chat(chat.id)
        if isadmin or (isallow and ismember) or (user.id in SUDO_USERS) or (user.id in DEV_USERS):
            connection_status = sql.connect(msg.from_user.id, chat.id)
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(msg, "Successfully connected to *{}*.".format(chat_name),
                             parse_mode=ParseMode.MARKDOWN)
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    bot.send_message(msg.from_user.id, f"You have connected with *{chat_name}*."
                                                       f" Use /connection for see current available commands.",
                                     parse_mode="markdown")
                except BadRequest:
                    pass
                except Unauthorized:
                    pass
            else:
                send_message(msg, "Connection failed!")
        else:
            send_message(msg, "Connection to this chat is not allowed!")


def disconnect_chat(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    spam = spamfilters(msg.text, msg.from_user.id, chat.id)
    if spam is True:
        return

    if chat.type == 'private':
        disconnection_status = sql.disconnect(msg.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = send_message(msg, "Disconnected from chat!")
        else:
            send_message(msg, "You're not connected!")
    else:
        send_message(msg, "This command is only available in PM.")


def connected(bot, update, chat, user_id, need_admin=True):
    user = update.effective_user
    msg = update.effective_message
    spam = spamfilters(msg.text, msg.from_user.id, update.effective_chat.id)

    if spam is True:
        return

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(conn_id, msg.from_user.id)
        isadmin = getstatusadmin.status in ADMIN_STATUS
        ismember = getstatusadmin.status in MEMBER_STAUS
        isallow = sql.allow_connect_to_chat(conn_id)

        if isadmin or (isallow and ismember) or (user.id in SUDO_USERS) or (user.id in DEV_USERS):
            if need_admin is True:
                if getstatusadmin.status in ADMIN_STATUS or user_id in SUDO_USERS or user.id in DEV_USERS:
                    return conn_id
                else:
                    send_message(msg, "You must be an admin in the connected group!")
                    raise Exception("Not admin!")
            else:
                return conn_id
        else:
            send_message(msg, "The group changed the connection rights or you are no longer an admin.\n"
                              "I've disconnected you.")
            disconnect_chat(bot, update)
            raise Exception("Not admin!")
    else:
        return False


@run_async
def help_connect_chat(bot: Bot, update: Update):
    msg = update.effective_message
    spam = spamfilters(msg.text, msg.from_user.id, update.effective_chat.id)
    if spam is True:
        return

    if msg.chat.type != "private":
        send_message(msg, "PM me with that command to get help.")
        return
    else:
        send_message(msg, "All commands", parse_mode="markdown")


@run_async
def connect_button(bot: Bot, update: Update):
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ADMIN_STATUS
        ismember = getstatusadmin.status in MEMBER_STAUS
        isallow = sql.allow_connect_to_chat(target_chat)

        if isadmin or (isallow and ismember) or (user.id in SUDO_USERS) or (user.id in DEV_USERS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_chat = dispatcher.bot.getChat(connected(bot, update, chat, user.id, need_admin=False))
                chat_name = conn_chat.title
                query.message.edit_text(f"Successfully connected to *{chat_name}*."
                                        f" Use /connection for see current available commands.",
                                        parse_mode=ParseMode.MARKDOWN)
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text("Connection failed!")
        else:
            bot.answer_callback_query(query.id, "Connection to this chat is not allowed!", show_alert=True)
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = query.message.edit_text("Disconnected from chat!")
        else:
            bot.answer_callback_query(query.id, "You're not connected!", show_alert=True)
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text("History connected has been cleared!")
    elif connect_close:
        query.message.edit_text("Closed.\nTo open again, type /connect")
    else:
        connect_chat(bot, update, [])


__help__ = """
 - /connect: connect a chat (Can be done in a group by /connect or /connect <chat id> in PM)
 - /connection: list connected chats
 - /disconnect: disconnect from a chat
 - /helpconnect: list available commands that can be done remotely

*Admin only:*
 - /allowconnect <yes/no>: allow a user to connect to a chat
"""

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, pass_args=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat)
ALLOW_CONNECTIONS_HANDLER = CommandHandler("allowconnect", allow_connections, pass_args=True)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect")

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)

__mod_name__ = "Connection"
__handlers__ = [CONNECT_CHAT_HANDLER, CONNECTION_CHAT_HANDLER, DISCONNECT_CHAT_HANDLER, ALLOW_CONNECTIONS_HANDLER,
                HELP_CONNECT_CHAT_HANDLER, CONNECT_BTN_HANDLER]
