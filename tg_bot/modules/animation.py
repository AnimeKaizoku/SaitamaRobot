import time
from telegram import Bot, Update
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
kamehameha_stickers = [
    'CAACAgUAAxkBAAIJnl7HbsxSakBMt5f0PuF6LsrJouqYAAKABwACT6I2L6so4G1Lr6ZJGQQ',
    'CAACAgUAAxkBAAIJn17Hbs7bGlIVFa7qnyhEhzpPg1ELAAKBBwACT6I2LzwXF1e4TjaBGQQ',
    'CAACAgUAAxkBAAIJoF7Hbs_vLME1JMJDtEVHJ1597oFUAAKCBwACT6I2L_yfBE_9nA1VGQQ',
    'CAACAgUAAxkBAAIJoV7HbtFY2OIUeqeOuxYd9bN8orfDAAKDBwACT6I2L-qppTkXolMiGQQ',
    'CAACAgUAAxkBAAIJol7HbtOKQb413CrlT9mmgVQDBdz3AAKEBwACT6I2L1KCKIMJlTt2GQQ',
    'CAACAgUAAxkBAAIJo17HbtVsWuJ1L9DhQo5ltyus0wABmAAChQcAAk-iNi-BeHflbIs0ChkE'
]
    
kamehameha_send_order = [1, 2, 3, 4, 5, 6, 5, 6, 5, 2, 1]

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
    msg.edit_text('FBI is here!')

@user_admin
@run_async
def kamehameha(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    for x in kamehameha_send_order:
        sticker_message = bot.send_sticker(chat_id, kamehameha_stickers[x])
        time.sleep(0.5)
        sticker_message.delete()
        


__help__ = """
- /police : Sends a police emoji animation. 
- /fbi : Send O\_O animation
- /kamehameha : Sends Stickers
"""
    
POLICE_HANDLER = DisableAbleCommandHandler("police", police)
FBI_HANDLER = DisableAbleCommandHandler("fbi", fbi)
KAMEHAMEHA_HANDLER = DisableAbleCommandHandler("kamehameha", kamehameha)
dispatcher.add_handler(KAMEHAMEHA_HANDLER)
dispatcher.add_handler(POLICE_HANDLER)    
dispatcher.add_handler(FBI_HANDLER)

__mod_name__ = "Animation"
__command_list__ = ["police", "fbi", "kamehameha"]	
__handlers__ = [POLICE_HANDLER, FBI_HANDLER, KAMEHAMEHA_HANDLER]
