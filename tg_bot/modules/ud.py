import requests
from telegram import Update, Bot, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler


@run_async
def ud(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/ud '):]
    results = requests.get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


__help__ = """
 - /ud <word>: Type the word or expression you want to search use.
 - /urban <word>: Same as /ud
"""

UD_HANDLER = DisableAbleCommandHandler(["ud", "urban"], ud)

dispatcher.add_handler(UD_HANDLER)

__mod_name__ = "Urban dictionary"
__command_list__ = ["ud", "urban"]
__handlers__ = [UD_HANDLER]
