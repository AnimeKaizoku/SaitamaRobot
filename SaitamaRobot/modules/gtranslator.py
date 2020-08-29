from emoji import UNICODE_EMOJI
from googletrans import LANGUAGES, Translator
from SaitamaRobot import dispatcher
from SaitamaRobot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async


@run_async
def totranslate(update: Update, context: CallbackContext):
    msg = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)
    try:
        if msg.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if msg.reply_to_message.text:
                text = msg.reply_to_message.text
            elif msg.reply_to_message.caption:
                text = msg.reply_to_message.caption

            message = update.effective_message
            dest_lang = None

            try:
                source_lang = args[1].split(None, 1)[0]
            except:
                source_lang = "en"

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
                        source_lang = None
                        break
                if dest_lang is None:
                    dest_lang = source_lang.split("-")[1]
                    source_lang = source_lang.split("-")[0]
            else:
                dest_lang = source_lang
                source_lang = None

            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')

            trl = Translator()
            if source_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=dest_lang)
                return message.reply_text(
                    f"Translated from `{detection.lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    f"Translated from `{source_lang}` to `{dest_lang}`:\n`{tekstr.text}`",
                    parse_mode=ParseMode.MARKDOWN)
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
            if dest_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        detection.lang, source_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    "Translated from `{}` to `{}`:\n`{}`".format(
                        source_lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(
            "Reply to messages or write messages from other languages ​​for translating into the intended language\n\n"
            "Example: `/tr en-ml` to translate from English to Malayalam\n"
            "Or use: `/tr ml` for automatic detection and translating it into Malayalam.\n"
            "See [List of Language Codes](t.me/OnePunchSupport/12823) for a list of language codes.",
            parse_mode="markdown",
            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(
            "The intended language is not found!")
    else:
        return


__help__ = """
• `/tr` or `/tl` (language code) as reply to a long message.
*Example:* `/tr en`*:* translates something to english. 
         `/tr hi-en`*:* translates hindi to english.
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], totranslate)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
