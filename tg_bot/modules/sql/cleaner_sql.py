import threading

from sqlalchemy import Column, UnicodeText, Boolean, Integer

from tg_bot.modules.sql import BASE, SESSION


class CleanerBlueText(BASE):
    __tablename__ = "cleaner_bluetext"

    chat_id = Column(UnicodeText, primary_key=True)
    is_enable = Column(Boolean, default=False)

    def __init__(self, chat_id, is_enable=True):
        self.chat_id = chat_id
        self.is_enable = is_enable

    def __repr__(self):
        return "clean blue text for {}".format(self.chat_id)


class CleanerIgnoreCommand(BASE):
    __tablename__ = "cleaner_ignore_commands"

    ignore_command = Column(UnicodeText, primary_key=True)

    def __init__(self, ignore_command):
        self.ignore_command = ignore_command


CleanerBlueText.__table__.create(checkfirst=True)
CleanerIgnoreCommand.__table__.create(checkfirst=True)
CLEANER_TEXT_INSERTION_LOCK = threading.RLock()
CLEANER_IGNORE_INSERTION_LOCK = threading.RLock()

CLEANER_BT_CHATS = []
IGNORE_COMMANDS = []


def is_enable(chat_id):
    return str(chat_id) in CLEANER_BT_CHATS


def set_cleanbt(chat_id, is_enable):
    with CLEANER_TEXT_INSERTION_LOCK:
        curr = SESSION.query(CleanerBlueText).get(str(chat_id))
        if not curr:
            curr = CleanerBlueText(str(chat_id), is_enable)
        else:
            curr.is_afk = is_enable

        if is_enable:
            if str(chat_id) not in CLEANER_BT_CHATS:
                CLEANER_BT_CHATS.append(str(chat_id))
        else:
            if str(chat_id) in CLEANER_BT_CHATS:
                CLEANER_BT_CHATS.remove(str(chat_id))

        SESSION.add(curr)
        SESSION.commit()


def add_clean_ignorecommand(ignore):
    with CLEANER_IGNORE_INSERTION_LOCK:
        ignored = SESSION.query(CleanerIgnoreCommand).get(str(ignore))

        if not ignored:
            IGNORE_COMMANDS.append(ignore)

            ignored = CleanerIgnoreCommand(str(ignore))
            SESSION.add(ignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def remove_clean_ignorecommand(unignore):
    with CLEANER_IGNORE_INSERTION_LOCK:
        ignored = SESSION.query(CleanerIgnoreCommand).get(str(unignore))

        if ignored:
            if unignore in IGNORE_COMMANDS:  # sanity check
                IGNORE_COMMANDS.remove(unignore)

            SESSION.delete(ignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def is_command_ignored(cmd):
    return str(cmd).lower() in IGNORE_COMMANDS


def get_all_ignored():
    return IGNORE_COMMANDS


def __load_cleaner_chats():
    global CLEANER_BT_CHATS
    try:
        all_chats = SESSION.query(CleanerBlueText).all()
        for x in all_chats:
            CLEANER_BT_CHATS.append(str(x.chat_id))
    finally:
        SESSION.close()


__load_cleaner_chats()
