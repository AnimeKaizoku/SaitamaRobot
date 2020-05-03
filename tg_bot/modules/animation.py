import time
from telegram import Bot, Update, ParseMode
from telegram.ext import run_async
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import user_admin

#sleep how many times after each edit in 'police' 
EDIT_SLEEP = 1
#edit how many times in 'police' 
EDIT_TIMES = 10

police_siren = [
            "🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵\n🔴🔴🔴⬜️⬜️⬜️🔵🔵🔵",
            "🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴\n🔵🔵🔵⬜️⬜️⬜️🔴🔴🔴"
]

@user_admin
@run_async
def police(bot: Bot, update: Update):
    msg = update.effective_message.reply_text('Police is coming!')
    for x in range(EDIT_TIMES):
        msg.edit_text(police_siren[x%2]) 
        time.sleep(EDIT_SLEEP)
    msg.edit_text('Police is here!')
    
__help__ = """
- /police : Sends a police emoji animation. 
"""
    
POLICE_HANDLER = DisableAbleCommandHandler("police", police)

dispatcher.add_handler(POLICE_HANDLER)    

__mod_name__ = "Animation"
__command_list__ = ["police"]	
__handlers__ = [POLICE_HANDLER]
