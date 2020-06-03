import re
import json
import urllib.request
import urllib.parse
import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError
from telegram import Message, Chat, Update, Bot, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
@run_async
def wiki(bot: Bot, update: Update):
    msg = update.effective_message.reply_to_message if update.effective_message.reply_to_message else update.effective_message
    res = ""
    if msg == update.effective_message:
        search = msg.text.split(" ", maxsplit=1)[1]
    else:
        search = msg.text
    try:
        res = wikipedia.summary(search)
    except DisambiguationError as e:
        update.message.reply_text("Disambiguated pages found! Adjust your query accordingly.\n<i>{}</i>".format(e),
        parse_mode=ParseMode.HTML)
    except PageError as e:
        update.message.reply_text("<code>{}</code>".format(e), parse_mode=ParseMode.HTML)
    if res:
        result = f"<b>{search}</b>\n\n"
        result += f"<i>{res}</i>\n"
        result += f"""<a href="https://en.wikipedia.org/wiki/{search.replace(" ", "%20")}">Read more...</a>"""
        if len(result) > 4000:
            with open("result.txt", 'w') as f:
                f.write(f"{result}\n\nUwU OwO OmO UmU")
            with open("result.txt", 'rb') as f:
                bot.send_document(document=f, filename=f.name,
                    reply_to_message_id=update.message.message_id, chat_id=update.effective_chat.id,
                    parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
__help__ = """
WIKIPEDIA!!
*Available commands:*
 - `/wiki <query>`*:* wiki your query.
"""

__mod_name__ = "Wiki"

WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
dispatcher.add_handler(WIKI_HANDLER)