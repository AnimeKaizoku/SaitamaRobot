import html
import subprocess
import importlib
import os
import json
import sys
import psutil
import requests
from typing import Optional, List
from time import sleep

from telegram import Message, Chat, Update, Bot, User
from telegram import ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_html
from tg_bot.__main__ import IMPORTED, HELPABLE, MIGRATEABLE, STATS, USER_INFO, DATA_IMPORT, DATA_EXPORT, CHAT_SETTINGS, USER_SETTINGS 

from tg_bot import dispatcher, LOGGER, SUDO_USERS, DEV_USERS, OWNER_ID, SUPPORT_USERS, WHITELIST_USERS, TOKEN
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, can_promote, user_admin, can_pin, sudo_plus, dev_plus
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.log_channel import loggable, gloggable

@run_async
@dev_plus
@gloggable
def addsudo(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    rt = ""
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("This member is already a Dragon Disaster")
        return ""
    if user_id in SUPPORT_USERS:
        rt += ("This user is already a Demon Disaster, Promoting to Dragon Disaster.")
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        rt += ("This user is already a Wolf, Promoting to Dragon Disaster.")
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)
    data['sudos'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    SUDO_USERS.append(user_id)
    update.effective_message.reply_text(rt + "\nSuccessfully set Disaster level of {} to Dragon!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))

@run_async
@dev_plus
@gloggable
def removesudo(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        message.reply_text("Demoting to normal user")
        SUDO_USERS.remove(user_id)
        data['sudos'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNSUDO" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a Dragon Disaster!")
        return ""

@run_async
@dev_plus
@gloggable
def addsupport(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    rt = ""
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        rt += ("Demoting status of this Dragon to Demon")
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)
    if user_id in SUPPORT_USERS:
        message.reply_text("This user is already a Demon Disaster.")
        return ""
    if user_id in WHITELIST_USERS:
        rt+=("Promoting Disaster level from Wolf to Demon")
        data['whitelists'].remove(user_id)
        WHITELIST_USERS.remove(user_id)
    data['supports'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    SUPPORT_USERS.append(user_id)
    update.effective_message.reply_text(rt + "\n{} was added as a Demon Disaster!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#SUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))

@run_async
@dev_plus
@gloggable
def removesupport(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUPPORT_USERS:
        message.reply_text("Demoting to Civilian")
        SUPPORT_USERS.remove(user_id)
        data['supports'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNSUPPORT" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a Demon level Disaster!")
        return ""

@run_async
@dev_plus
@gloggable
def addwhitelist(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    rt = ""
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in SUDO_USERS:
        rt += ("This member is a Dragon Disaster, Demoting to Wolf.")
        data['sudos'].remove(user_id)
        SUDO_USERS.remove(user_id)
    if user_id in SUPPORT_USERS:
        rt += ("This user is already a Demon Disaster, Demoting to Wolf.")
        data['supports'].remove(user_id)
        SUPPORT_USERS.remove(user_id)
    if user_id in WHITELIST_USERS:
        message.reply_text("This user is already a Wolf Disaster.")
        return ""
    data['whitelists'].append(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
        json.dump(data, outfile, indent=4)
    WHITELIST_USERS.append(user_id)
    update.effective_message.reply_text(rt + "\nSuccessfully promoted {} to a Wolf Disaster!".format(user_member.user.first_name))
    return "<b>{}:</b>" \
           "\n#WHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))

@run_async
@dev_plus
@gloggable
def removewhitelist(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message
    user = update.effective_user
    user_id = extract_user(message, args)
    user_member = update.effective_chat.get_member(user_id)
    with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'r') as infile:
        data = json.load(infile)
    if user_id in WHITELIST_USERS:
        message.reply_text("Demoting to normal user")
        WHITELIST_USERS.remove(user_id)
        data['whitelists'].remove(user_id)
        with open('{}/tg_bot/elevated_users.json'.format(os.getcwd()), 'w') as outfile:
            json.dump(data, outfile, indent=4)
        return "<b>{}:</b>" \
           "\n#UNWHITELIST" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(update.effective_chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))
    else:
        message.reply_text("This user is not a Wolf Disaster!")
        return ""

@run_async
@sudo_plus
def gitpull(bot: Bot, update: Update):
    sent_msg = update.effective_message.reply_text("Pulling all changes from remote and then attempting to restart.")
    p = subprocess.Popen('git pull', stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nChanges pulled...I guess.. Restarting in "

    sent_msg.edit_text(sent_msg_text+"5")

    sleep(1)
    sent_msg.edit_text(sent_msg_text+"4")

    sleep(1)
    sent_msg.edit_text(sent_msg_text+"3")

    sleep(1)
    sent_msg.edit_text(sent_msg_text+"2")

    sleep(1)
    sent_msg.edit_text(sent_msg_text+"1")
    sleep(1)
    sent_msg.edit_text("Restarted.")
    
    os.system('restart.bat')
    os.execv('start.bat', sys.argv)

@run_async
@sudo_plus
def restart(bot: Bot, update: Update):
    update.effective_message.reply_text("Starting a new instance and shutting down this one")
    os.system('restart.bat')
    os.execv('start.bat', sys.argv)

@run_async
@sudo_plus
def load(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/load '):]
    message.reply_text("Attempting to load a new module")
    imported_module = importlib.import_module("tg_bot.modules." + text)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    update.effective_message.reply_text("Successfully loaded module: {}".format(text))
    

@run_async
@bot_admin
@can_promote
@user_admin
@loggable
def promote(bot: Bot, update: Update, args: List[str]) -> str:
    chat_id = update.effective_chat.id
    message = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'administrator' or user_member.status == 'creator':
        message.reply_text("How am I meant to promote someone that's already an admin?")
        return ""

    if user_id == bot.id:
        message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return ""

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    bot.promoteChatMember(chat_id, user_id,
                          can_change_info=bot_member.can_change_info,
                          can_post_messages=bot_member.can_post_messages,
                          can_edit_messages=bot_member.can_edit_messages,
                          can_delete_messages=bot_member.can_delete_messages,
                          can_invite_users=bot_member.can_invite_users,
                          # can_promote_members=bot_member.can_promote_members,
                          can_restrict_members=bot_member.can_restrict_members,
                          can_pin_messages=bot_member.can_pin_messages)
                         

    message.reply_text("Successfully promoted!")
    return "<b>{}:</b>" \
           "\n#PROMOTED" \
           "\n<b>Admin:</b> {}" \
           "\n<b>User:</b> {}".format(html.escape(chat.title),
                                      mention_html(user.id, user.first_name),
                                      mention_html(user_member.user.id, user_member.user.first_name))


@run_async
@bot_admin
@can_promote
@user_admin
@loggable
def demote(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text("This person CREATED the chat, how would I demote them?")
        return ""

    if not user_member.status == 'administrator':
        message.reply_text("Can't demote what wasn't promoted!")
        return ""

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return ""

    try:
        bot.promoteChatMember(int(chat.id), int(user_id),
                              can_change_info=False,
                              can_post_messages=False,
                              can_edit_messages=False,
                              can_delete_messages=False,
                              can_invite_users=False,
                              can_restrict_members=False,
                              can_pin_messages=False,
                              can_promote_members=False)
        message.reply_text("Successfully demoted!")
        return "<b>{}:</b>" \
               "\n#DEMOTED" \
               "\n<b>Admin:</b> {}" \
               "\n<b>User:</b> {}".format(html.escape(chat.title),
                                          mention_html(user.id, user.first_name),
                                          mention_html(user_member.user.id, user_member.user.first_name))

    except BadRequest:
        message.reply_text("Could not demote. I might not be admin, or the admin status was appointed by another "
                           "user, so I can't act upon them!")
        return ""

#Until the library releases the method
@run_async
@bot_admin
@can_promote
@user_admin
def set_title(bot: Bot, update: Update, args: List[str]):

    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    user_id, title = extract_user_and_text(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_member = chat.get_member(user_id)
    if user_member.status == 'creator':
        message.reply_text("This person CREATED the chat, how can i set custom title for him?")
        return ""

    if not user_member.status == 'administrator':
        message.reply_text("Can't set title for non-admins!\nPromote them first to set custom title!")
        return

    if user_id == bot.id:
        message.reply_text("I can't set my own title myself! Get the one who made me admin to do it for me.")
        return

    result = requests.post(f"https://api.telegram.org/bot{TOKEN}/setChatAdministratorCustomTitle?chat_id={chat.id}&user_id={user_id}&custom_title={title}")
    status = result.json()["ok"]

    if status == True:
        message.reply_text("Successfully set the custom title!")
    else:
        description = result.json()["description"]
        if description == "Bad Request: not enough rights to change custom title of the user":
            message.reply_text("I can't set custom title for admins that I didn't promote!")

@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(bot: Bot, update: Update, args: List[str]) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    is_group = chat.type != "private" and chat.type != "channel"

    prev_message = update.effective_message.reply_to_message

    is_silent = True
    if len(args) >= 1:
        is_silent = not (args[0].lower() == 'notify' or args[0].lower() == 'loud' or args[0].lower() == 'violent')

    if prev_message and is_group:
        try:
            bot.pinChatMessage(chat.id, prev_message.message_id, disable_notification=is_silent)
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        return "<b>{}:</b>" \
               "\n#PINNED" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(bot: Bot, update: Update) -> str:
    chat = update.effective_chat
    user = update.effective_user  # type: Optional[User]

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    return "<b>{}:</b>" \
           "\n#UNPINNED" \
           "\n<b>Admin:</b> {}".format(html.escape(chat.title),
                                       mention_html(user.id, user.first_name))


@run_async
@bot_admin
@user_admin
def invite(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.username:
        update.effective_message.reply_text(chat.username)
    elif chat.type == chat.SUPERGROUP or chat.type == chat.CHANNEL:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text("I don't have access to the invite link, try changing my permissions!")
    else:
        update.effective_message.reply_text("I can only give you invite links for supergroups and channels, sorry!")


@run_async
def adminlist(bot: Bot, update: Update):
    administrators = update.effective_chat.get_administrators()
    text = "Admins in *{}*:".format(update.effective_chat.title or "this chat")
    for admin in administrators:
        user = admin.user
        name = "[{}](tg://user?id={})".format(user.first_name + (user.last_name or ""), user.id)
        text += "\n - {}".format(name)

    update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


def __chat_settings__(chat_id, user_id):
    return "You are *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status in ("administrator", "creator"))


__help__ = """
 - /adminlist: list of admins in the chat

*Admin only:*
 - /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifs to users.
 - /unpin: unpins the currently pinned message
 - /invitelink: gets invitelink
 - /promote: promotes the user replied to
 - /demote: demotes the user replied to
"""

__mod_name__ = "Admin"

PIN_HANDLER = CommandHandler("pin", pin, pass_args=True, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

GITPULL_HANDLER = CommandHandler("gitpull", gitpull, filters=Filters.group)
RESTART_HANDLER = CommandHandler("restart", restart, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite, filters=Filters.group)

PROMOTE_HANDLER = CommandHandler("promote", promote, pass_args=True, filters=Filters.group)
DEMOTE_HANDLER = CommandHandler("demote", demote, pass_args=True, filters=Filters.group)

SET_TITLE_HANDLER = CommandHandler("settitle", set_title, pass_args=True, filters=Filters.group)

ADMINLIST_HANDLER = DisableAbleCommandHandler("adminlist", adminlist, filters=Filters.group)
LOAD_HANDLER = CommandHandler("load", load, filters=Filters.group)

SUDO_HANDLER = CommandHandler(("addsudo", "adddragon"), addsudo, pass_args=True, filters=Filters.group)
UNSUDO_HANDLER = CommandHandler(("removesudo", "removedragon"), removesudo, pass_args=True, filters=Filters.group)
SUPPORT_HANDLER = CommandHandler(("addsupport", "adddemon"), addsupport, pass_args=True, filters=Filters.group)
UNSUPPORT_HANDLER = CommandHandler(("removesupport", "removedemon"), removesupport, pass_args=True, filters=Filters.group)
WHITELIST_HANDLER = CommandHandler(("addwhitelist", "addwolf"), addwhitelist, pass_args=True, filters=Filters.group)
UNWHITELIST_HANDLER = CommandHandler(("removewhitelist", "removewolf"), removewhitelist, pass_args=True, filters=Filters.group)

dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(LOAD_HANDLER)
dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(SUDO_HANDLER)
dispatcher.add_handler(UNSUDO_HANDLER)
dispatcher.add_handler(SUPPORT_HANDLER)
dispatcher.add_handler(UNSUPPORT_HANDLER)
dispatcher.add_handler(WHITELIST_HANDLER)
dispatcher.add_handler(UNWHITELIST_HANDLER)
