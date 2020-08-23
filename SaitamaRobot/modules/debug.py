import os
import datetime

from telethon import events
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, run_async

from SaitamaRobot import telethn, dispatcher
from SaitamaRobot.modules.helper_funcs.chat_status import dev_plus

DEBUG_MODE = False

@telethn.on(events.NewMessage(pattern="[/!].*"))
async def i_do_nothing_yes(event):
    if DEBUG_MODE:
        if os.path.exists('updates.txt'):
            with open('updates.txt', 'r') as f:
                text = f.read()
            with open('updates.txt', 'w+') as f:
                f.write(text + f"\n-{event.from_id} ({event.chat_id}) : {event.text}")
        else:
            with open('updates.txt', 'w+') as f:
                f.write(f"- {event.from_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}")

@run_async
@dev_plus
def debug(update: Update, context: CallbackContext):
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    if len(args) > 1:
        if args[1] in ('yes', 'on'):
            DEBUG_MODE = True
        elif args[1] in ('no', 'off'):
            DEBUG_MODE = False 
    else:
        if DEBUG_MODE:
            message.reply_text("Debug mode is currently off.")
        else:
            message.reply_text("Debug mode is currently on.")

DEBUG_HANDLER = CommandHandler("debug", debug)
dispatcher.add_handler(DEBUG_HANDLER)

__mod_name__ = "Debug"
__command_list__ = ["debug"]
__handlers__ = [
    DEBUG_HANDLER
]
