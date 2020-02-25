from telegram import Bot, Update, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher, WHITELIST_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import whitelist_plus


@run_async
@whitelist_plus
def whitelistlist(bot: Bot, update: Update):

    reply = "<b>Wolf Disasters 🐺:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            first_name = user.first_name
            reply += """• <a href="tg://user?id={}">{}</a>\n""".format(user_id, first_name)
        except:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


@run_async
@whitelist_plus
def supportlist(bot: Bot, update: Update):

    reply = "<b>Demon Disasters 👹:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            first_name = user.first_name
            reply += """• <a href="tg://user?id={}">{}</a>\n""".format(user_id, first_name)
        except:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)



@run_async
@whitelist_plus
def sudolist(bot: Bot, update: Update):

    reply = "<b>Dragon Disasters 🐉:</b>\n"
    for each_user in SUDO_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            first_name = user.first_name
            reply += """• <a href="tg://user?id={}">{}</a>\n""".format(user_id, first_name)
        except:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)



@run_async
@whitelist_plus
def devlist(bot: Bot, update: Update):

    reply = "<b>Hero Association Members ⚡️:</b>\n"
    for each_user in DEV_USERS:
        user_id = int(each_user)
        try:
            user = bot.get_chat(user_id)
            first_name = user.first_name
            reply += """• <a href="tg://user?id={}">{}</a>\n""".format(user_id, first_name)
        except:
            pass
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = """
 - /whitelistlist - List whitelisted users.
 - /supportlist - List support users.
 - /sudolist - List sudo users.
 - /devlist - List dev users.
"""

WHITELISTLIST_HANDLER = DisableAbleCommandHandler(["whitelistlist", "wolves"], whitelistlist)
SUPPORTLIST_HANDLER = DisableAbleCommandHandler(["supportlist", "demons"], supportlist)
SUDOLIST_HANDLER = DisableAbleCommandHandler(["sudolist", "dragons"], sudolist)
DEVLIST_HANDLER = DisableAbleCommandHandler(["devlist", "heroes"], devlist)

dispatcher.add_handler(WHITELISTLIST_HANDLER)
dispatcher.add_handler(SUPPORTLIST_HANDLER)
dispatcher.add_handler(SUDOLIST_HANDLER)
dispatcher.add_handler(DEVLIST_HANDLER)

__mod_name__ = "Disasters"
__command_list__ = ["whitelistlist", "wolves", "supportlist", "demons", "sudolist", "dragons", "devlist", "heroes"]
__handlers__ = [WHITELISTLIST_HANDLER, SUPPORTLIST_HANDLER, SUDOLIST_HANDLER, DEVLIST_HANDLER]
