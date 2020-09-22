from telegram import Update

from telegram.ext import CallbackContext, run_async, CommandHandler

from SaitamaRobot import dispatcher

from SaitamaRobot.modules.helper_funcs.chat_status import dev_plus


@run_async
@dev_plus
def logs(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = message.chat_id
    if chat_id != -1001408942668:
        return
    user = update.effective_user
    with open('log.txt', 'rb') as f:

        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


LOG_HANDLER = CommandHandler('logs', logs)

dispatcher.add_handler(LOG_HANDLER)
