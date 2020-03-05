# Module to blacklist users and prevent them from using commands by @TheRealPhoenix

from telegram import Message, User, Bot, Update, ParseMode
from telegram.ext import CommandHandler, run_async, Filters

from tg_bot import dispatcher, OWNER_ID
from tg_bot import OWNER_ID as oi, DEV_USERS as du, SUDO_USERS as su, WHITELIST_USERS as wu, SUPPORT_USERS as gb
import tg_bot.modules.sql.blacklistusers_sql as sql

BLACKLISTWHITELIST = du + su + wu + gb
BLACKLISTWHITELIST.insert(0, oi)
BLABLEUSERS = du
@run_async
def bl_user(bot: Bot, update: Update, args):
    if update.effective_message.reply_to_message:
        user_id = str(update.effective_message.reply_to_message.from_user.id)
        reason = " ".join(args)
    else:
        user_id = args[0]
        reason = " ".join(args[1:])
    if int(user_id) in BLACKLISTWHITELIST:
            update.effective_message.reply_text("No!\nNoticing Disasters is my job.")
            return False
    sql.blacklist_user(user_id, reason)
    update.effective_message.reply_text("I shall ignore the existence of this user!")
    

@run_async 
def bl_users(bot: Bot, update: Update):
    rep = "<b>Blacklisted Users</b>\n"
    for x in sql.BLACKLIST_USERS:
        name = bot.get_chat(x)
        name = name.first_name.replace("<", "&lt;")
        name = name.replace(">", "&gt;")
        reason = sql.get_reason(x)
        if reason:
            rep += f"• <a href='tg://user?id={x}'>{name}</a> :- {reason}\n"
        else:
            rep += f"• <a href='tg://user?id={x}'>{name}</a>\n"
    if rep == "<b>Blacklisted Users</b>\n":
        rep += "Noone is being ignored as of yet."
    update.effective_message.reply_text(rep, parse_mode=ParseMode.HTML)
    
    
@run_async
def unbl_user(bot: Bot, update: Update, args):
    rep = update.effective_message
    msg = update.effective_message.reply_to_message
    if msg:
        user_id = str(msg.from_user.id)
    else:
        user_id = args[0]
    if sql.is_user_blacklisted(int(user_id)):
        sql.unblacklist_user(user_id)
        rep.reply_text("*notices user*")
    else:
        rep.reply_text("I am not ignoring them at all though!")
        
        
def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)
    
    text = "Blacklisted: <b>{}</b>"
    if is_blacklisted:
        text = text.format("Yes")
        reason = sql.get_reason(user_id)
        if reason:
            text += f"\nReason: <code>{reason}</code>"
    else:
        text = text.format("No")
    return text
           
    
BL_HANDLER = CommandHandler("ignore", bl_user, pass_args=True, filters=Filters.user(BLABLEUSERS))
UNBL_HANDLER = CommandHandler("notice", unbl_user, pass_args=True, filters=Filters.user(BLABLEUSERS))
BLUSERS_HANDLER = CommandHandler("ignoredlist", bl_users, filters=Filters.user(BLABLEUSERS))

dispatcher.add_handler(BL_HANDLER)
dispatcher.add_handler(UNBL_HANDLER)
dispatcher.add_handler(BLUSERS_HANDLER)
