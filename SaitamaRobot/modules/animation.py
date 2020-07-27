import time

from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin
from telegram import Update
from telegram.ext import CallbackContext, run_async

#sleep how many times after each edit in 'police'
EDIT_SLEEP = 2
#edit how many times in 'police'
EDIT_TIMES = 3

POLICE_SIREN = [
    "🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵",
    "🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴"
]


@user_admin
@run_async
def police(update: Update, context: CallbackContext):
    msg = update.effective_message.reply_text('Police is coming!')
    for x in range(EDIT_TIMES):
        msg.edit_text(POLICE_SIREN[x % 2])
        time.sleep(EDIT_SLEEP)
    msg.edit_text('Police is here!')


__help__ = """
• `/police`*:* Sends a police emoji animation. 
"""

POLICE_HANDLER = DisableAbleCommandHandler("police", police)
dispatcher.add_handler(POLICE_HANDLER)

__mod_name__ = "Animation"
__command_list__ = ["police"]
__handlers__ = [POLICE_HANDLER]
