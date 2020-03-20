import speedtest
from telegram import Update, Bot, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import dev_plus

@dev_plus
@run_async
def speedtestxyz(bot: Bot, update: Update):
    s = speedtest.Speedtest()
    msg = update.effective_message.reply_text("Doing SpeedTest.... ")
    s.get_best_server()
    s.download()
    s.upload()
    speedtest_image = s.results.share()
    update.effective_message.reply_photo(photo=speedtest_image, caption='Done!')
    msg.delete()
SpeedTest_handler = DisableAbleCommandHandler("speedtest", speedtestxyz)
dispatcher.add_handler(SpeedTest_handler)

__mod_name__ = "SpeedTest"
