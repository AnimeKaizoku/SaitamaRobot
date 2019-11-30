from telegram import Update, Bot, User, ParseMode
from telegram.ext import run_async

from tg_bot import dispatcher
from tg_bot.modules.disable import DisableAbleCommandHandler

from emoji import UNICODE_EMOJI
from googletrans import Translator, LANGUAGES

@run_async
def totranslate(bot: Bot, update: Update):
	msg = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)
    try:
        if msg.reply_to_message and msg.reply_to_message.text:
            args = update.effective_message.text.split(None, 1)
            text = msg.reply_to_message.text
            message = update.effective_message
            dest_lang = None
            try:
                source_lang = args[1].split(None, 1)[0]
            except:
                source_lang = args[1]
            if source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        if source_lang.startswith(lang):
                            dest_lang = source_lang.rsplit("-", 1)[1]
                            source_lang = source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = source_lang.split("-", 1)[1]
                            source_lang = source_lang.split("-", 1)[0]
            elif source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        dest_lang = source_lang
                    else:
                        dest_lang = source_lang.split("-")[1]
                        source_lang = source_lang.split("-")[0]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            trl = Translator()
            if dest_lang == None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, source_lang, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(source_lang, dest_lang, tekstr.text), parse_mode=ParseMode.MARKDOWN)
        else:
            args = update.effective_message.text.split(None, 2)
            message = update.effective_message
            source_lang = args[1]
            text = args[2]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            dest_lang = None
            temp_source_lang = source_lang
            if temp_source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        if temp_source_lang.startswith(lang):
                            dest_lang = temp_source_lang.rsplit("-", 1)[1]
                            source_lang = temp_source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = temp_source_lang.split("-", 1)[1]
                            source_lang = temp_source_lang.split("-", 1)[0]
            elif temp_source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        dest_lang = None
                        break
                    else:
                        dest_lang = temp_source_lang.split("-")[1]
                        source_lang = temp_source_lang.split("-")[0]
            trl = Translator()
            if dest_lang == None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, source_lang, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(source_lang, dest_lang, tekstr.text), parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text("Reply to messages or write messages from other languages ​​for translating into the intended language\n\nExample: `/tr en-ml` to translate from English to Malayalam\nOr use: `/tr ml` for automatic detection and translating it into Malayalam", parse_mode="markdown")
    except ValueError:
        update.effective_message.reply_text("The intended language is not found!")
    else:
        return

__help__ = """- /tr (language code) as reply to a long message.
"""
__mod_name__ = "Translator"

TOTRANSLATE_HANDLER = DisableAbleCommandHandler("tr", totranslate)

dispatcher.add_handler(TOTRANSLATE_HANDLER)
