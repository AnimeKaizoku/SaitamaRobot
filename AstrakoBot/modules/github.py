import html
from typing import Optional, List

import tg_bot.modules.helper_funcs.git_api as api

from tg_bot import dispatcher, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS
from tg_bot.modules.helper_funcs.filters import CustomFilters

from telegram.ext import CommandHandler, run_async, Filters

from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

@run_async
def getRelease(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args)<1):
        msg.reply_text("Please specify a combination of <user>/<repo>")
        return
    url = args[0]
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    recentRelease = api.getLastestReleaseData(api.getData(url))
    author = api.getAuthor(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "Author: "+author+"\n"
    message += "Release Name: "+releaseName+"\n\n"
    for asset in assets:
        message += "*Asset:* \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "[{}]({})".format(fileName, fileURL)
        sizeB = ((api.getSize(asset))/1024)/1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n" 
    msg.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    return

__help__ = """
Github module. This module will fetch github releases.
Commands:
 - /git <user>/<repo>: will fetch the most recent release from that repo.
"""

__mod_name__ = "Github"



RELEASEHANDLER = CommandHandler("git", getRelease, pass_args=True)

dispatcher.add_handler(RELEASEHANDLER)
