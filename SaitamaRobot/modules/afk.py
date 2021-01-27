import random
from time import sleep

from telegram import MessageEntity
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async

import Elizabeth.modules.helper_funcs.fun_strings as fun
from Elizabeth import dispatcher
from Elizabeth.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from Elizabeth.modules.sql import afk_sql as sql
from Elizabeth.modules.users import get_user_id

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


@run_async
def afk(update, context):
    args = update.effective_message.text.split(None, 1)
    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    afkstr = random.choice(fun.AFK)
    msg = update.effective_message
    afksend = msg.reply_text(
        afkstr.format(
            update.effective_user.first_name,
            notice))
    sleep(5)
    afksend.delete()


@run_async
def no_longer_afk(update, context):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    res = sql.rm_afk(user.id)
    if res:
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "Where is {}?\nIn the chat!",
            ]
            chosen_option = random.choice(options)
            unafk = update.effective_message.reply_text(
                chosen_option.format(firstname))
            sleep(10)
            unafk.delete()
        except BaseException:
            return


@run_async
def reply_afk(update, context):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(
                    message.text[ent.offset: ent.offset + ent.length]
                )
                if not user_id:
                    # Should never happen, since for a user to become AFK they
                    # must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print(
                        "Error: Could not fetch userid {} for AFK module".format(
                            user_id
                        )
                    )
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if sql.is_afk(user_id):
        user = sql.check_afk_status(user_id)
        if not user.reason:
            if int(userc_id) == int(user_id):
                return
            res = "{} is afk".format(fst_name)
            noreason = update.effective_message.reply_text(res)
            sleep(10)
            noreason.delete()
        else:
            if int(userc_id) == int(user_id):
                return
            res = "<b>{}</b> is away from keyboard! says it's because of <b>Reason:</b> <code>{}</code>".format(
                fst_name, user.reason)
            replafk = update.effective_message.reply_text(
                res, parse_mode="html")
            sleep(10)
            replafk.delete()


def __gdpr__(user_id):
    sql.rm_afk(user_id)


AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)brb"), afk, friendly="afk"
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(
    Filters.all & Filters.group & ~Filters.update.edited_message, reply_afk
)


dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)


__mod_name__ = "AFK"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
