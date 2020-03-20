import importlib
from typing import Union, List

from future.utils import string_types
from telegram import Bot, Update, ParseMode
from telegram.ext import CommandHandler, RegexHandler, MessageHandler
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS, CustomCommandHandler
from tg_bot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):

    from telegram.ext.dispatcher import run_async

    from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin, connection_status
    from tg_bot.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []


    class DisableAbleCommandHandler(CustomCommandHandler):

        def __init__(self, command, callback, admin_ok=False, filters=None, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            self.filters = filters
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            chat = update.effective_chat
            user = update.effective_user

            if super().check_update(update):

                # Should be safe since check_update passed.
                command = update.effective_message.text_html.split(None, 1)[0][1:].split('@')[0]

                # disabled, admincmd, user admin
                if sql.is_command_disabled(chat.id, command):
                    if command in ADMIN_CMDS and is_user_admin(chat, user.id):
                        return True

                # not disabled
                else:
                    return True


    class DisableAbleMessageHandler(MessageHandler):
        def __init__(self, filters, callback, friendly, **kwargs):
            super().__init__(filters, callback, **kwargs)
            DISABLE_OTHER.append(friendly)
            self.friendly = friendly
            self.filters = filters

        def check_update(self, update):

            chat = update.effective_chat
            if super().check_update(update):
                if sql.is_command_disabled(chat.id, self.friendly):
                    return False
                else:
                    return True


    class DisableAbleRegexHandler(RegexHandler):
        def __init__(self, pattern, callback, friendly="", filters=None, **kwargs):
            super().__init__(pattern, callback, filters, **kwargs)
            DISABLE_OTHER.append(friendly)
            self.friendly = friendly

        def check_update(self, update):
            chat = update.effective_chat
            if super().check_update(update):
                if sql.is_command_disabled(chat.id, self.friendly):
                    return False
                else:
                    return True


    @run_async
    @connection_status
    @user_admin
    def disable(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, str(disable_cmd).lower())
                update.effective_message.reply_text(f"Disabled the use of `{disable_cmd}`",
                                                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text("That command can't be disabled")

        else:
            update.effective_message.reply_text("What should I disable?")


    @run_async
    @connection_status
    @user_admin
    def disable_module(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat
        if len(args) >= 1:
            disable_module = "tg_bot.modules." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(disable_module)
            except:
                update.effective_message.reply_text("Does that module even exist?")
                return

            try:
                command_list = module.__command_list__
            except:
                update.effective_message.reply_text("Module does not contain command list!")
                return

            disabled_cmds = []
            failed_disabled_cmds = []

            for disable_cmd in command_list:
                if disable_cmd.startswith(CMD_STARTERS):
                    disable_cmd = disable_cmd[1:]

                if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                    sql.disable_command(chat.id, str(disable_cmd).lower())
                    disabled_cmds.append(disable_cmd)
                else:
                    failed_disabled_cmds.append(disable_cmd)

            if disabled_cmds:
                disabled_cmds_string = ", ".join(disabled_cmds)
                update.effective_message.reply_text(f"Disabled the uses of `{disabled_cmds_string}`",
                                                    parse_mode=ParseMode.MARKDOWN)

            if failed_disabled_cmds:
                failed_disabled_cmds_string = ", ".join(failed_disabled_cmds)
                update.effective_message.reply_text(f"Commands `{failed_disabled_cmds_string}` can't be disabled",
                                                    parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("What should I disable?")


    @run_async
    @connection_status
    @user_admin
    def enable(bot: Bot, update: Update, args: List[str]):

        chat = update.effective_chat
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                update.effective_message.reply_text(f"Enabled the use of `{enable_cmd}`",
                                                    parse_mode=ParseMode.MARKDOWN)
            else:
                update.effective_message.reply_text("Is that even disabled?")

        else:
            update.effective_message.reply_text("What should I enable?")


    @run_async
    @connection_status
    @user_admin
    def enable_module(bot: Bot, update: Update, args: List[str]):
        chat = update.effective_chat

        if len(args) >= 1:
            enable_module = "tg_bot.modules." + args[0].rsplit(".", 1)[0]

            try:
                module = importlib.import_module(enable_module)
            except:
                update.effective_message.reply_text("Does that module even exist?")
                return

            try:
                command_list = module.__command_list__
            except:
                update.effective_message.reply_text("Module does not contain command list!")
                return

            enabled_cmds = []
            failed_enabled_cmds = []

            for enable_cmd in command_list:
                if enable_cmd.startswith(CMD_STARTERS):
                    enable_cmd = enable_cmd[1:]

                if sql.enable_command(chat.id, enable_cmd):
                    enabled_cmds.append(enable_cmd)
                else:
                    failed_enabled_cmds.append(enable_cmd)

            if enabled_cmds:
                enabled_cmds_string = ", ".join(enabled_cmds)
                update.effective_message.reply_text(f"Enabled the uses of `{enabled_cmds_string}`",
                                                    parse_mode=ParseMode.MARKDOWN)

            if failed_enabled_cmds:
                failed_enabled_cmds_string = ", ".join(failed_enabled_cmds)
                update.effective_message.reply_text(f"Are the commands `{failed_enabled_cmds_string}` even disabled?",
                                                    parse_mode=ParseMode.MARKDOWN)

        else:
            update.effective_message.reply_text("What should I enable?")


    @run_async
    @connection_status
    @user_admin
    def list_cmds(bot: Bot, update: Update):
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += f" - `{escape_markdown(cmd)}`\n"
            update.effective_message.reply_text(f"The following commands are toggleable:\n{result}",
                                                parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text("No commands can be disabled.")


    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return "The following commands are currently restricted:\n{}".format(result)


    @run_async
    @connection_status
    def commands(bot: Bot, update: Update):
        chat = update.effective_chat
        update.effective_message.reply_text(build_curr_disabled(chat.id), parse_mode=ParseMode.MARKDOWN)


    def __stats__():
        return f"{sql.num_disabled()} disabled items, across {sql.num_chats()} chats."


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        return build_curr_disabled(chat_id)


    DISABLE_HANDLER = CommandHandler("disable", disable, pass_args=True)
    DISABLE_MODULE_HANDLER = CommandHandler("disablemodule", disable_module, pass_args=True)
    ENABLE_HANDLER = CommandHandler("enable", enable, pass_args=True)
    ENABLE_MODULE_HANDLER = CommandHandler("enablemodule", enable_module, pass_args=True)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds)

    dispatcher.add_handler(DISABLE_HANDLER)
    dispatcher.add_handler(DISABLE_MODULE_HANDLER)
    dispatcher.add_handler(ENABLE_HANDLER)
    dispatcher.add_handler(ENABLE_MODULE_HANDLER)
    dispatcher.add_handler(COMMANDS_HANDLER)
    dispatcher.add_handler(TOGGLE_HANDLER)

    __help__ = """
    - /cmds: check the current status of disabled commands

    *Admin only:*
    - /enable <cmd name>: enable that command
    - /disable <cmd name>: disable that command
    - /enablemodule <module name>: enable all commands in that module
    - /disablemodule <module name>: disable all commands in that module
    - /listcmds: list all possible toggleable commands
    """

    __mod_name__ = "Command disabling"

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleRegexHandler = RegexHandler
    DisableAbleMessageHandler = MessageHandler
