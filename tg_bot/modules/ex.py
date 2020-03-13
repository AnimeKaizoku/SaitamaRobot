import requests

from typing import Optional, List

from telegram import Update, Bot, ParseMode

from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler

from tg_bot import dispatcher
import speedtest

from tg_bot.modules.helper_funcs.chat_status import dev_plus

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

    reply_text = 'Nekofied to *Nekobin* : {}'.format(url)

    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)

@dev_plus
@run_async 
def speedtest(bot: Bot, update: Update):
  s = speedtest.Speedtest()
  s.get_best_server()
  s.download()
  s.upload()
  speedtest_image = s.results.share() 
  update.effective_message.reply_photo(photo=speedtest_image, caption = 'Done!')

PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, pass_args=True)
SpeedTest_handler = DisableAbleCommandHandler("speedtest", speedtest)
dispatcher.add_handler(SpeedTest_handler)
dispatcher.add_handler(PASTE_HANDLER)

