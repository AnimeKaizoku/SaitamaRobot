import threading

from SaitamaRobot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, UnicodeText


class CleanerBlueTextChatSettings(BASE):
    __tablename__ = "cleaner_bluetext_chat_setting"
    chat_id = Column(UnicodeText, primary_key=True)
    is_enable = Column(Boolean, default=False)

    def __init__(self, chat_id, is_enable):
        self.chat_id = chat_id
        self.is_enable = is_enable

    def __repr__(self):
        return "clean blue text for {}".format(self.chat_id)


class CleanerBlueTextChat(BASE):
    __tablename__ = "cleaner_bluetext_chat_ignore_commands"
    chat_id = Column(UnicodeText, primary_key=True)
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, command):
        self.chat_id = chat_id
        self.command = command


class CleanerBlueTextGlobal(BASE):
    __tablename__ = "cleaner_bluetext_global_ignore_commands"
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, command):
        self.command = command


CleanerBlueTextChatSettings.__table__.create(checkfirst=True)
CleanerBlueTextChat.__table__.create(checkfirst=True)
CleanerBlueTextGlobal.__table__.create(checkfirst=True)

CLEANER_CHAT_SETTINGS = threading.RLock()
CLEANER_CHAT_LOCK = threading.RLock()
CLEANER_GLOBAL_LOCK = threading.RLock()

CLEANER_CHATS = {}
GLOBAL_IGNORE_COMMANDS = set()


def set_cleanbt(chat_id, is_enable):
    with CLEANER_CHAT_SETTINGS:
        curr = SESSION.query(CleanerBlueTextChatSettings).get(str(chat_id))

        if not curr:
            curr = CleanerBlueTextChatSettings(str(chat_id), is_enable)
        else:
            curr.is_enabled = is_enable

        if str(chat_id) not in CLEANER_CHATS:
            CLEANER_CHATS.setdefault(
                str(chat_id), {
                    "setting": False,
                    "commands": set()
                })

        CLEANER_CHATS[str(chat_id)]["setting"] = is_enable

        SESSION.add(curr)
        SESSION.commit()


def chat_ignore_command(chat_id, ignore):
    ignore = ignore.lower()
    with CLEANER_CHAT_LOCK:
        ignored = SESSION.query(CleanerBlueTextChat).get((str(chat_id), ignore))

        if not ignored:

            if str(chat_id) not in CLEANER_CHATS:
                CLEANER_CHATS.setdefault(
                    str(chat_id), {
                        "setting": False,
                        "commands": set()
                    })

            CLEANER_CHATS[str(chat_id)]["commands"].add(ignore)

            ignored = CleanerBlueTextChat(str(chat_id), ignore)
            SESSION.add(ignored)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def chat_unignore_command(chat_id, unignore):
    unignore = unignore.lower()
    with CLEANER_CHAT_LOCK:
        unignored = SESSION.query(CleanerBlueTextChat).get(
            (str(chat_id), unignore))

        if unignored:

            if str(chat_id) not in CLEANER_CHATS:
                CLEANER_CHATS.setdefault(
                    str(chat_id), {
                        "setting": False,
                        "commands": set()
                    })
            if unignore in CLEANER_CHATS.get(str(chat_id)).get("commands"):
                CLEANER_CHATS[str(chat_id)]["commands"].remove(unignore)

            SESSION.delete(unignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def global_ignore_command(command):
    command = command.lower()
    with CLEANER_GLOBAL_LOCK:
        ignored = SESSION.query(CleanerBlueTextGlobal).get(str(command))

        if not ignored:
            GLOBAL_IGNORE_COMMANDS.add(command)

            ignored = CleanerBlueTextGlobal(str(command))
            SESSION.add(ignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def global_unignore_command(command):
    command = command.lower()
    with CLEANER_GLOBAL_LOCK:
        unignored = SESSION.query(CleanerBlueTextGlobal).get(str(command))

        if unignored:
            if command in GLOBAL_IGNORE_COMMANDS:
                GLOBAL_IGNORE_COMMANDS.remove(command)

            SESSION.delete(command)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def is_command_ignored(chat_id, command):
    if command.lower() in GLOBAL_IGNORE_COMMANDS:
        return True

    if str(chat_id) in CLEANER_CHATS:
        if command.lower() in CLEANER_CHATS.get(str(chat_id)).get('commands'):
            return True

    return False


def is_enabled(chat_id):
    if str(chat_id) in CLEANER_CHATS:
        settings = CLEANER_CHATS.get(str(chat_id)).get('setting')
        return settings

    return False


def get_all_ignored(chat_id):
    if str(chat_id) in CLEANER_CHATS:
        LOCAL_IGNORE_COMMANDS = CLEANER_CHATS.get(str(chat_id)).get("commands")
    else:
        LOCAL_IGNORE_COMMANDS = set()

    return GLOBAL_IGNORE_COMMANDS, LOCAL_IGNORE_COMMANDS


def __load_cleaner_list():
    global GLOBAL_IGNORE_COMMANDS
    global CLEANER_CHATS

    try:
        GLOBAL_IGNORE_COMMANDS = {
            int(x.command) for x in SESSION.query(CleanerBlueTextGlobal).all()
        }
    finally:
        SESSION.close()

    try:
        for x in SESSION.query(CleanerBlueTextChatSettings).all():
            CLEANER_CHATS.setdefault(x.chat_id, {
                "setting": False,
                "commands": set()
            })
            CLEANER_CHATS[x.chat_id]["setting"] = x.is_enable
    finally:
        SESSION.close()

    try:
        for x in SESSION.query(CleanerBlueTextChat).all():
            CLEANER_CHATS.setdefault(x.chat_id, {
                "setting": False,
                "commands": set()
            })
            CLEANER_CHATS[x.chat_id]["commands"].add(x.command)
    finally:
        SESSION.close()


__load_cleaner_list()
