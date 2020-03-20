import speedtest
from telegram import Update, Bot, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import run_async, CallbackQueryHandler
from tg_bot import DEV_USERS as devs
from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import dev_plus

def convert(speed):
	return round(int(speed)/1048576, 2)

@dev_plus
@run_async
def speedtestxyz(bot: Bot, update: Update):
 buttons = [
        [InlineKeyboardButton("Image", callback_data="speedtest_image"), InlineKeyboardButton("Text", callback_data="speedtest_text")]
    ]
 update.effective_message.reply_text("Select SpeedTest Mode",
                                        reply_markup=InlineKeyboardMarkup(buttons))

@run_async
def speedtestxyz_callback(bot: Bot, update: Update):
    query = update.callback_query
    if query.from_user.id in devs:
     s = speedtest.Speedtest()
     s.get_best_server()
     s.download()
     s.upload()
     replymsg = 'SpeedTest Results:'
     if query.data == 'speedtest_image':
      speedtest_image = s.results.share()
      update.effective_message.reply_photo(photo=speedtest_image, caption=replymsg)
     elif query.data == 'speedtest_text':
      result = s.results.dict()
      replymsg += f"Download: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
      update.effective_message.edit_text(replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
       query.answer("You are not allowed to use this.")


__mod_name__ = "SpeedTest"
SpeedTest_handler = DisableAbleCommandHandler("speedtest", speedtestxyz)
SpeedTest_callbackhandler = CallbackQueryHandler(speedtestxyz_callback, pattern='speedtest_.*')
dispatcher.add_handler(SpeedTest_handler)
dispatcher.add_handler(SpeedTest_callbackhandler)
