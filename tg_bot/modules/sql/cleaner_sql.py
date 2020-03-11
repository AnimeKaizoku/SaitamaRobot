import threading

from sqlalchemy import Column, UnicodeText, Boolean, Integer

from emilia.modules.sql import BASE, SESSION


class CleanerBlueText(BASE):
    __tablename__ = "cleaner_bluetext"

    chat_id = Column(UnicodeText, primary_key=True)
    is_enable = Column(Boolean, default=False)

    def __init__(self, chat_id, is_enable=True):
        self.chat_id = chat_id
        self.is_enable = is_enable

    def __repr__(self):
        return "clean blue text for {}".format(self.chat_id)


CleanerBlueText.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()

CLEANER_BT_CHATS = []


def is_enable(chat_id):
    return str(chat_id) in CLEANER_BT_CHATS


def set_cleanbt(chat_id, is_enable):
    with INSERTION_LOCK:
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


def __load_cleaner_chats():
    global CLEANER_BT_CHATS
    try:
        all_chats = SESSION.query(CleanerBlueText).all()
        for x in all_chats:
            CLEANER_BT_CHATS.append(str(x.chat_id))
    finally:
        SESSION.close()


__load_cleaner_chats()