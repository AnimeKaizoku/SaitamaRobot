import requests

from typing import Optional, List

from telegram import Update, Bot, ParseMode

from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler

from tg_bot import dispatcher

def paste(bot: Bot, update: Update, args: List[str]):

    message = update.effective_message

    if message.reply_to_message:

        data = message.reply_to_message.text

    elif len(args) >= 1:

        data = message.text.split(None, 1)[1]

    else:

        message.reply_text("What am I supposed to do with this?")

        return

    key = requests.post('https://nekobin.com/api/documents', json = {"content": data}).json().get('result').get('key')

    url = 'https://nekobin.com/' + key

    reply_text = 'Nekofied to Nekobin : `{}`'.format(url)

    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

   

PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, pass_args=True)

dispatcher.add_handler(PASTE_HANDLER)

