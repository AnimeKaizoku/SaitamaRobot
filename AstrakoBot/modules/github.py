import html
from typing import Optional, List

import AstrakoBot.modules.helper_funcs.git_api as api
import AstrakoBot.modules.sql.github_sql as sql

from AstrakoBot import dispatcher, OWNER_ID, EVENT_LOGS, DRAGONS, DEMONS
from AstrakoBot.modules.helper_funcs.filters import CustomFilters
from AstrakoBot.modules.helper_funcs.chat_status import user_admin
from AstrakoBot.modules.disable import DisableAbleCommandHandler

from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, RegexHandler, run_async)

from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, MAX_MESSAGE_LENGTH

#do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "*Author:* [{}]({})\n".format(author, authorUrl)
    message += "*Release Name:* "+releaseName+"\n\n"
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
        return repo.value, repo.backoffset
    return None, None

@run_async
def getRelease(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) == 0:
        msg.reply_text("Please use some arguments!")
        return
    if(len(args) != 1 and not (len(args) == 2 and args[1].isdigit()) and not ("/" in args[0])):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return

@run_async
def hashFetch(update: Update, context: CallbackContext): #kanged from notes
    bot, args = context.bot, context.args
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url, index = getRepo(bot, update, no_hash)
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request. Likely this is not a saved repo shortcut", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return
    
@run_async
def cmdFetch(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0])
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request. Likely this is not a saved repo shortcut", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return
    
@run_async
def changelog(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    msg.reply_text(body)
    return
    
    
@run_async
@user_admin
def saveRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args) != 2 and (len(args) != 3 and not args[2].isdigit()) or not ("/" in args[1])):
        msg.reply_text("Invalid data, use <reponame> <user>/<repo> <value (optional)>")
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
    msg.reply_text("Repo shortcut saved successfully!")
    return
    
@run_async
@user_admin
def delRepo(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args)!=1):
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    msg.reply_text("Repo shortcut deleted successfully!")
    return
    
@run_async
def listRepo(update: Update, context: CallbackContext):
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
        
def getVer(update: Update, context: CallbackContext):
    msg = update.effective_message
    ver = api.vercheck()
    msg.reply_text("GitHub API version: "+ver)
    return

__help__ = """
*Github module. This module will fetch github releases*\n
*Available commands:*
 • `/git <user>/<repo>`: will fetch the most recent release from that repo.
 • `/git <user>/<repo> <number>`: will fetch releases in past.
 • `/fetch <reponame> or &reponame`: same as `/git`, but you can use a saved repo shortcut
 • `/listrepo`: lists all repo shortcuts in chat
 • `/gitver`: returns the current API version
 • `/changelog <reponame>`: gets the changelog of a saved repo shortcut
 
*Admin only:*
 • `/saverepo <name> <user>/<repo> <number (optional)>`: saves a repo value as shortcut
 • `/delrepo <name>`: deletes a repo shortcut
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
