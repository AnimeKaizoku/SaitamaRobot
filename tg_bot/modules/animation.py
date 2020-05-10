import time
from telegram import Bot, Update, ParseMode
from telegram.ext import run_async
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin

#sleep how many times after each edit in 'police' 
EDIT_SLEEP = 2
#edit how many times in 'police' 
EDIT_TIMES = 3

police_siren = [
            "🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵",
            "🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴"
]

fbi_ig = [
  "\O_O",
  "O_O/"
]

@user_admin
@run_async
def police(bot: Bot, update: Update):
    msg = update.effective_message.reply_text('Police is coming!')
    for x in range(EDIT_TIMES):
        msg.edit_text(police_siren[x%2]) 
        time.sleep(EDIT_SLEEP)
    msg.edit_text('Police is here!')

@user_admin
@run_async
def fbi(bot: Bot, update: Update):
    msg = update.effective_message.reply_text('FBI is coming!')
    for x in range(EDIT_TIMES):
        msg.edit_text(fbi_ig[x%2]) 
        time.sleep(EDIT_SLEEP)
    msg.edit_text('Police is here!')
    
__help__ = """
- /police : Sends a police emoji animation. 
- /fbi : Send O_O animation
"""
    
POLICE_HANDLER = DisableAbleCommandHandler("police", police)
FBI_HANDLER = DisableAbleCommandHandler("fbi", fbi)
dispatcher.add_handler(POLICE_HANDLER)    
dispatcher.add_handler(FBI_HANDLER)

__mod_name__ = "Animation"
__command_list__ = ["police", "fbi"]	
__handlers__ = [POLICE_HANDLER, FBI_HANDLER]
