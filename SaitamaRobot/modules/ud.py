import requests
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async


@run_async
def ud(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text[len('/ud '):]
    results = requests.get(
        f'https://api.urbandictionary.com/v0/define?term={text}').json()
    try:
        reply_text = f'*{text}*\n\n{results["list"][0]["definition"]}\n\n_{results["list"][0]["example"]}_'
    except:
        reply_text = "No results found."
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)


__help__ = """
 • `/ud <word>`*:* Type the word or expression you want to search use.
"""

UD_HANDLER = DisableAbleCommandHandler(["ud"], ud)

dispatcher.add_handler(UD_HANDLER)

__mod_name__ = "Urban dictionary"
__command_list__ = ["ud"]
__handlers__ = [UD_HANDLER]
