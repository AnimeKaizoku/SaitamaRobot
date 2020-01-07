import html
from typing import Optional, List

import tg_bot.modules.helper_funcs.git_api as api
import tg_bot.modules.sql.github_sql as sql

from tg_bot import dispatcher, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.chat_status import user_admin
from tg_bot.modules.disable import DisableAbleCommandHandler

from telegram.ext import CommandHandler, run_async, Filters, RegexHandler

from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, MAX_MESSAGE_LENGTH

#do not async
def getData(url):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getLastestReleaseData(api.getData(url))
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "Author: [{}]({})\n".format(author, authorUrl)
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
    return message

#likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value
    return None

@run_async
def getRelease(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    url = args[0]
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return

@run_async
def hashFetch(bot: Bot, update: Update): #kanged from notes
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url = getRepo(bot, update, no_hash)
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return
    
@run_async
def cmdFetch(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url = getRepo(bot, update, args[0])
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return
    
@run_async
def changelog(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getLastestReleaseData(data)
    body = api.getBody(release)
    msg.reply_text(body)
    return
    
    
@run_async
@user_admin
def saveRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args) != 2):
        msg.reply_text("Invalid data, use <reponame> <user>/<repo>")
        return
    sql.add_repo_to_db(str(chat_id), args[0], args[1])
    msg.reply_text("Repo shortcut saved successfully!")
    return
    
@run_async
@user_admin
def delRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args)!=1):
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    msg.reply_text("Repo shortcut deleted successfully!")
    return
    
@run_async
def listRepo(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "*List of repo shotcuts in {}:*\n"
    des = "You can get repo shortcuts by using `/fetch repo`, or `&repo`.\n"
    for repo in repo_list:
        repo_name = (" • `{}`\n".format(repo.name))
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += repo_name
    if msg == "*List of repo shotcuts in {}:*\n":
        update.effective_message.reply_text("No repo shortcuts in this chat!")
    elif len(msg) != 0:
        update.effective_message.reply_text(msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN)
        
def getVer(bot: Bot, update: Update):
    msg = update.effective_message
    ver = api.vercheck()
    msg.reply_text("GitHub API version: "+ver)
    return

__help__ = """
Github module. This module will fetch github releases.
Commands:
 - /git <user>/<repo>: will fetch the most recent release from that repo.
 - /fetch <reponame> or &reponame: same as /git, but you can use a saved repo shortcut
 - /listrepo: lists all repo shortcuts in chat
 - /gitver: returns the current API version
 - /changelog <reponame>: gets the changelog of a saved repo shortcut
 
Admin only:
 - /saverepo <name> <user>/<repo>: saves a repo value as shortcut
 - /delrepo <name>: deletes a repo shortcut
"""

__mod_name__ = "GitHub"



RELEASE_HANDLER = DisableAbleCommandHandler("git", getRelease, pass_args=True, admin_ok=True)
FETCH_HANDLER = DisableAbleCommandHandler("fetch", cmdFetch, pass_args=True, admin_ok=True)
SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo, pass_args=True)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo, pass_args=True)
LISTREPO_HANDLER = DisableAbleCommandHandler("listrepo", listRepo, admin_ok=True)
VERCHECKER_HANDLER = DisableAbleCommandHandler("gitver", getVer, admin_ok=True)
CHANGELOG_HANDLER = DisableAbleCommandHandler("changelog", changelog, pass_args=True, admin_ok=True)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)
