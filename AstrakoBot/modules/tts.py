import html, os
import re
from datetime import datetime
from typing import List
import random
from telegram import ChatAction
from gtts import gTTS
import time
from telegram import ChatAction
from feedparser import parse
import json
import urllib.request
import urllib.parse
import requests
from AstrakoBot import DEV_USERS, OWNER_ID, DRAGONS, DEMONS, WOLVES, dispatcher, updater
from AstrakoBot.__main__ import STATS, TOKEN, USER_INFO
from AstrakoBot.modules.disable import DisableAbleCommandHandler
from AstrakoBot.modules.helper_funcs.filters import CustomFilters
from AstrakoBot.modules.helper_funcs.chat_status import sudo_plus, user_admin
from AstrakoBot.modules.helper_funcs.extraction import extract_user
from telegram import MessageEntity, ParseMode, Update, constants
from telegram.error import BadRequest
from emoji import UNICODE_EMOJI
from AstrakoBot.modules.helper_funcs.alternate import typing_action
from wikipedia.exceptions import DisambiguationError, PageError
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html


@run_async
def tts(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message
    reply = ""
    if message.reply_to_message:
        reply = message.reply_to_message.text

    if args:
        reply = "  ".join(args).lower()

    current_time = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    filename = datetime.now().strftime("%d%m%y-%H%M%S%f")
    update.message.chat.send_action(ChatAction.RECORD_AUDIO)
    lang = "ml"
    tts = gTTS(reply, lang)
    tts.save("k.mp3")
    with open("k.mp3", "rb") as f:
        linelist = list(f)
        linecount = len(linelist)
    if linecount == 1:
        update.message.chat.send_action(ChatAction.RECORD_AUDIO)
        lang = "en"
        tts = gTTS(reply, lang)
        tts.save("k.mp3")
    with open("k.mp3", "rb") as speech:
        update.message.reply_voice(speech, quote=False)

    os.remove("k.mp3")


TTS_HANDLER = DisableAbleCommandHandler("tts", tts, pass_args=True)
dispatcher.add_handler(TTS_HANDLER)

__handlers__ = [TTS_HANDLER]
