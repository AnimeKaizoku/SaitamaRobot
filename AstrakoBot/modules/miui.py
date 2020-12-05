from time import sleep
from requests import get
from yaml import load, Loader
from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot import dispatcher, updater, CallbackContext
from tg_bot.modules.disable import DisableAbleCommandHandler


URL = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/latest.yml"

def delete(msg, delmsg, timer):
    sleep(timer)
    try:
        msg.delete()
        delmsg.delete()
    except:
        return

def miui(update: Update, context: CallbackContext):
    args = context.args
    msg = update.effective_message

    codename = args[0] if len(args) > 0 else False

    if not codename:
        delmsg = msg.reply_text("Provide a codename bruh!")
        delete(msg, delmsg, 5)
        return

    yaml_data = load(get(URL).content, Loader=Loader)
    data = [ i for i in yaml_data if codename in i['codename'] ]

    if len(data) < 1:
        delmsg = msg.reply_text("Provide a valid codename bruh!")
        delete(msg, delmsg, 5)
        return

    markup = []
    for fw in data:
        av = fw['android']
        branch = fw['branch']
        method = fw['method']
        link = fw['link']
        fname = fw['name']
        version = fw['version']

        btn = fname + ' | ' + branch + ' | ' + method + ' | ' + version
        markup.append([InlineKeyboardButton(text=btn, url=link)])

    device = fname.split(" ")
    device.pop()
    device = " ".join(device)
    delmsg = msg.reply_text(f"The latest firmwares for *{device}* are:",
                            reply_markup=InlineKeyboardMarkup(markup),
                            parse_mode=ParseMode.MARKDOWN)
    delete(msg, delmsg, 60)

__help__ = """
*MiUI related commands:*

 - /miui codename - fetches latest firmware info for <codename>

 *Examples:*
  /miui lmi

*Note:* The messages are auto deleted to prevent group flooding. Incorrect codenames are deleted after 5 seconds and correct codenames are deleted after 60 seconds.
"""

__mod_name__ = "MiUI"

MIUI_HANDLER = DisableAbleCommandHandler("miui", miui, run_async=True)

dispatcher.add_handler(MIUI_HANDLER)
