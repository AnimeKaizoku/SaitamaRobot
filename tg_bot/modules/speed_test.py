import speedtest
from telegram import Update, Bot, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import run_async, CallbackQueryHandler

from tg_bot import dispatcher, DEV_USERS
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

    if query.from_user.id in DEV_USERS:
        msg = update.effective_message.edit_text('Runing a speedtest....') 
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = 'SpeedTest Results:'

        if query.data == 'speedtest_image':
            speedtest_image = speed.results.share()
            update.effective_message.reply_photo(photo=speedtest_image, caption=replymsg)
            msg.delete()

        elif query.data == 'speedtest_text':
            result = speed.results.dict()
            replymsg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            update.effective_message.edit_text(replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        query.answer("You are required to join Heroes Association to use this command.")


SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(speedtestxyz_callback, pattern='speedtest_.*')

dispatcher.add_handler(SPEED_TEST_HANDLER)
dispatcher.add_handler(SPEED_TEST_CALLBACKHANDLER)

__mod_name__ = "SpeedTest"
__command_list__ = ["speedtest"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER]
