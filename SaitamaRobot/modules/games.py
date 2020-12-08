import html
import random
import time

from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async
from telegram.error import BadRequest

import SaitamaRobot.modules.fun_strings as fun_strings
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from SaitamaRobot.modules.helper_funcs.chat_status import (is_user_admin)
from SaitamaRobot.modules.helper_funcs.extraction import extract_user


@run_async
def truth(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.TRUTH_STRINGS))


@run_async
def dare(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.DARE_STRINGS))


@run_async
def tord(update: Update, context: CallbackContext):
    update.effective_message.reply_text(random.choice(fun_strings.TORD_STRINGS))

"""
 __help__ = 
 • `/truth`*:* asks you a question
 • `/dare`*:* gives you a dare
 • `/tord`*:* can be a truth or a dare
 
 """

TRUTH_HANDLER = DisableAbleCommandHandler("truth", truth)
DARE_HANDLER = DisableAbleCommandHandler("dare", dare)
TORD_HANDLER = DisableAbleCommandHandler("tord", tord)


dispatcher.add_handler(TRUTH_HANDLER)
dispatcher.add_handler(DARE_HANDLER)
dispatcher.add_handler(TORD_HANDLER)


__mod_name__ = "Games"
__command_list__ = [
   "truth", "dare", "tord",
]

__handlers__ = [
    TRUTH_HANDLER, DARE_HANDLER, TORD_HANDLER,
]
