from telegram import Update, Bot, ParseMode
from telegram.ext import CommandHandler, CallbackContext, run_async

import AstrakoBot.modules.sql.private_notes as sql
from AstrakoBot import dispatcher
from AstrakoBot.modules.helper_funcs.chat_status import user_admin


@user_admin
def privatenotes(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    msg = ""

    if message.chat.type == "private":
        msg = "This command is meant to use in group not in PM"

    elif len(args) == 0:
        setting = getprivatenotes(chat.id)
        msg = f"Private notes value is *{setting}* in *{chat.title}*"

    elif len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0", "disable", "false"]:
            setprivatenotes(chat.id, False)
            msg = f"Private notes has been disabled in *{chat.title}*"
        elif val in ["on", "yes", "1", "enable", "true"]:
            setprivatenotes(chat.id, True)
            msg = f"Private notes has been enabled in *{chat.title}*"
        else: 
            msg = "Sorry, wrong value"

    message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN
    )

def setprivatenotes(chat_id, setting):
    sql.set_private_notes(chat_id, setting)
            

def getprivatenotes(chat_id):
    setting = sql.get_private_notes(chat_id)
    return setting



PRIVATENOTES_HANDLER = CommandHandler("privatenotes", privatenotes, run_async=True)

dispatcher.add_handler(PRIVATENOTES_HANDLER)
