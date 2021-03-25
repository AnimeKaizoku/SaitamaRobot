from telegram import Update, Bot, ParseMode
from telegram.ext import CommandHandler, CallbackContext, run_async

import AstrakoBot.modules.sql.private_notes as sql
from AstrakoBot import dispatcher
from AstrakoBot.modules.helper_funcs.chat_status import user_admin
from AstrakoBot.modules.helper_funcs.alternate import send_message


@user_admin
def privatenotes(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if update.effective_message.chat.type == "private":
        send_message(
            update.effective_message,
            "This command is meant to use in group not in PM",
        )
        return ""

    if len(args) == 0:
        setting = getprivatenotes(chat.id)
        send_message(
            update.effective_message, "Private notes value is {} in *{}*.".format(setting, chat.title),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0", "disable", "false"]:
            setprivatenotes(chat.id, False)
            send_message(
                update.effective_message, "Private notes has been disabled in *{}*".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
            )
        elif val in ["on", "yes", "1", "enable", "true"]:
            setprivatenotes(chat.id, True)
            send_message(
                update.effective_message, "Private notes has been enabled in *{}*".format(chat.title),
                parse_mode=ParseMode.MARKDOWN,
            )
        else: 
            send_message(
                update.effective_message, "Sorry, wrong value"
            )

def setprivatenotes(chat_id, setting):
    sql.set_private_notes(chat_id, setting)
            

def getprivatenotes(chat_id):
    setting = sql.get_private_notes(chat_id)
    return setting



PRIVATENOTES_HANDLER = CommandHandler("privatenotes", privatenotes, run_async=True)

dispatcher.add_handler(PRIVATENOTES_HANDLER)
