from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import MessageEntity
from telegram.ext import Filters, MessageHandler, run_async
from telegram import ParseMode

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from emoji import UNICODE_EMOJI

from googletrans import Translator


@run_async
def totranslate(bot: Bot, update: Update):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	"""
	lang = str("af,am,ar,az,be,bg,bn,bs,ca,ceb,co,cs,cy,da,de,el,en,eo,es,et,eu,fa,fi,fr,fy,ga,gd,gl,gu,ha,haw,hi,hmn,hr,ht,hu,hy,id,ig,is,it,iw,ja,jw,ka,kk,km,kn,ko,ku,ky,la,lb,lo,lt,lv,mg,mi,mk,ml,mn,mr,ms,mt,my,ne,nl,no,ny,pa,pl,ps,pt,ro,ru,sd,si,sk,sl,sm,sn,so,sq,sr,st,su,sv,sw,ta,te,tg,th,tl,tr,uk,ur,uz,vi,xh,yi,yo,zh,zh_CN,zh_TW,zu".split(","))
	try:
		if msg.reply_to_message and msg.reply_to_message.text:
			args = update.effective_message.text.split(None, 1)
			try:
				target = args[1].split(None, 1)[0]
			except:
				target = args[1]
			try:
				target2 = args[1].split(None, 2)[1]
				if target2 not in lang:
					target2 = None
				else:
					target = args[1].split(None, 2)[0]
					target2 = args[1].split(None, 2)[1]
			except:
				target2 = None
			text = msg.reply_to_message.text
			message = update.effective_message
			trl = Translator()
			if target2 == None:
				detection = trl.detect(text)
				tekstr = trl.translate(text, dest=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n*Characters:*\n`{}`\n*Text:*\n`{}`".format(detection.lang, target, tekstr.text, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(text, dest=target2, src=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n*Characters:*\n`{}`\n*Text:*\n`{}`".format(target, target2, tekstr.text, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			
		else:
			args = update.effective_message.text.split(None, 2)
			target = args[1]
			try:
				target2 = args[2].split(None, 1)[0]
				if target2 not in lang:
					target2 = None
					text = args[2]
				else:
					target2 = args[2].split(None, 1)[0]
					text = args[2].split(None, 1)[1]
			except:
				target2 = None
				text = args[2]
			message = update.effective_message
			trl = Translator()
			if target2 == None:
				detection = trl.detect(text)
				tekstr = trl.translate(text, dest=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n*Characters:*\n`{}`\n*Text:*\n`{}`".format(detection.lang, target, tekstr.text, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(text, dest=target2, src=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n*Characters:*\n`{}`\n*Text:*\n`{}`".format(target, target2, tekstr.text, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
	"""
	try:
		if msg.reply_to_message and msg.reply_to_message.text:
			args = update.effective_message.text.split(None, 1)
			target2 = None
			try:
				target = args[1].split(None, 1)[0]
			except:
				target = args[1]
			if "-" in target:
				target2 = target.split("-")[1]
				target = target.split("-")[0]
			text = msg.reply_to_message.text
			#text = deEmojify(text)
			exclude_list = UNICODE_EMOJI.keys()
			for emoji in exclude_list:
				if emoji in text:
					text = text.replace(emoji, '')
			message = update.effective_message
			trl = Translator()
			if target2 == None:
				detection = trl.detect(text)
				tekstr = trl.translate(text, dest=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(text, dest=target2, src=target)
				if tekstr.pronunciation == None:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				else:
					return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			
		else:
			args = update.effective_message.text.split(None, 2)
			target = args[1]
			text = args[2]
			#text = deEmojify(text)
			exclude_list = UNICODE_EMOJI.keys()
			for emoji in exclude_list:
				if emoji in text:
					text = text.replace(emoji, '')
			target2 = None
			if "-" in target:
				target2 = target.split("-")[1]
				target = target.split("-")[0]
			message = update.effective_message
			trl = Translator()
			if target2 == None:
				detection = trl.detect(text)
				tekstr = trl.translate(text, dest=target)
				return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				#if tekstr.pronunciation == None:
				#	return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				#else:
				#	return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(detection.lang, target, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(text, dest=target2, src=target)
				message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				#if tekstr.pronunciation == None:
				#	return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
				#else:
				#	return message.reply_text("Translated from `{}` to `{}`:\n`{}`".format(target, target2, tekstr.pronunciation), parse_mode=ParseMode.MARKDOWN)
				
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
