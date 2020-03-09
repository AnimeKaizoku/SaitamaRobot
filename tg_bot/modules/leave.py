from typing import List

from telegram import Bot, Update, TelegramError
from telegram.ext import CommandHandler, run_async

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import dev_plus


@run_async
@dev_plus
def leave(bot: Bot, update: Update, args: List[str]):

    if args:
        chat_id = str(args[0])
        try:
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Beep boop, I left that soup!.")
        except TelegramError:
            update.effective_message.reply_text("Beep boop, I could not leave that group(dunno why tho).")
    else:
        update.effective_message.reply_text("Send a valid chat ID") 

LEAVE_HANDLER = CommandHandler("leave", leave, pass_args = True)

dispatcher.add_handler(LEAVE_HANDLER)

__mod_name__ = "Leave"
__handlers__ = [LEAVE_HANDLER]
