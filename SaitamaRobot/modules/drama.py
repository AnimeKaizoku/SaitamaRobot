import datetime
import html
import textwrap

import bs4
import jikanpy
import requests
from SaitamaRobot import DEV_USERS, OWNER_ID, DRAGONS, dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async

info_btn = "More Information"


def site_search(update: Update, context: CallbackContext, site: str):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    more_results = True

    try:
        search_query = args[1]
    except IndexError:
        message.reply_text("Give something to search")
        return

    if site == "MyDramaList":
        search_url = f"https://mydramalist.com/search?q=={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h1", {'class':"title"})

    if search_result:
            result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>MyDramaList</code>: \n"
            for entry in search_result:
                post_link = "https://mydramalist.com/" + entry.a['href']
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
  
    elif site == "mydl":
        search_url = f"https://mydramalist.com/search?q={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h1", {'class': "title"})

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>MyDramaList</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>MyDramaList</code>"
                more_results = False
                break

            post_link = entry.a['href']
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = [[InlineKeyboardButton("See all results", url=search_url)]]

    if more_results:
        message.reply_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)
    else:
        message.reply_text(
            result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
def drama(update: Update, context: CallbackContext):
    site_search(update, context, "mdl")


@run_async
def mydl(update: Update, context: CallbackContext):
    site_search(update, context, "mydl")


__help__ = """
Get information about anime, manga or characters from [MDL](mydramalist.com).

*Available commands:*

 • `/drama <drama>`*:* returns information about the anime.
 • `/mydl <drama>`*:* search an drama on MDL

 """

DRAMA_HANDLER = DisableAbleCommandHandler("drama", drama)
MYDL_SEARCH_HANDLER = DisableAbleCommandHandler("mydl", mydl)
BUTTON_HANDLER = CallbackQueryHandler(button, pattern='anime_.*')

dispatcher.add_handler(BUTTON_HANDLER)
dispatcher.add_handler(DRAMA_SEARCH_HANDLER)
dispatcher.add_handler(MYDL_SEARCH_HANDLER)

__mod_name__ = "Drama"
__command_list__ = [
    "drama", "mydl"
   ]
   
__handlers__ = [
    DRAMA_HANDLER, MYDL_SEARCH_HANDLER,
    BUTTON_HANDLER
   ]
