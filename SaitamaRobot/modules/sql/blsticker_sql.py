import threading

from SaitamaRobot.modules.sql import BASE, SESSION
from sqlalchemy import Column, Integer, String, UnicodeText, distinct, func


class StickersFilters(BASE):
    __tablename__ = "blacklist_stickers"
    chat_id = Column(String(14), primary_key=True)
    trigger = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, chat_id, trigger):
        self.chat_id = str(chat_id)  # ensure string
        self.trigger = trigger

    def __repr__(self):
        return "<Stickers filter '%s' for %s>" % (self.trigger, self.chat_id)

    def __eq__(self, other):
        return bool(
            isinstance(other, StickersFilters) and
            self.chat_id == other.chat_id and self.trigger == other.trigger)


class StickerSettings(BASE):
    __tablename__ = "blsticker_settings"
    chat_id = Column(String(14), primary_key=True)
    blacklist_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id, blacklist_type=1, value="0"):
        self.chat_id = str(chat_id)
        self.blacklist_type = blacklist_type
        self.value = value

    def __repr__(self):
        return "<{} will executing {} for blacklist trigger.>".format(
            self.chat_id, self.blacklist_type)


StickersFilters.__table__.create(checkfirst=True)
StickerSettings.__table__.create(checkfirst=True)

STICKERS_FILTER_INSERTION_LOCK = threading.RLock()
STICKSET_FILTER_INSERTION_LOCK = threading.RLock()

CHAT_STICKERS = {}
CHAT_BLSTICK_BLACKLISTS = {}


def add_to_stickers(chat_id, trigger):
    with STICKERS_FILTER_INSERTION_LOCK:
        stickers_filt = StickersFilters(str(chat_id), trigger)

        SESSION.merge(stickers_filt)  # merge to avoid duplicate key issues
        SESSION.commit()
        global CHAT_STICKERS
        if CHAT_STICKERS.get(str(chat_id), set()) == set():
            CHAT_STICKERS[str(chat_id)] = {trigger}
        else:
            CHAT_STICKERS.get(str(chat_id), set()).add(trigger)


def rm_from_stickers(chat_id, trigger):
    with STICKERS_FILTER_INSERTION_LOCK:
        stickers_filt = SESSION.query(StickersFilters).get(
            (str(chat_id), trigger))
        if stickers_filt:
            if trigger in CHAT_STICKERS.get(str(chat_id),
                                            set()):  # sanity check
                CHAT_STICKERS.get(str(chat_id), set()).remove(trigger)

            SESSION.delete(stickers_filt)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_chat_stickers(chat_id):
    return CHAT_STICKERS.get(str(chat_id), set())


def num_stickers_filters():
    try:
        return SESSION.query(StickersFilters).count()
    finally:
        SESSION.close()


def num_stickers_chat_filters(chat_id):
    try:
        return (SESSION.query(StickersFilters.chat_id).filter(
            StickersFilters.chat_id == str(chat_id)).count())
    finally:
        SESSION.close()


def num_stickers_filter_chats():
    try:
        return SESSION.query(func.count(distinct(
            StickersFilters.chat_id))).scalar()
    finally:
        SESSION.close()


def set_blacklist_strength(chat_id, blacklist_type, value):
    # for blacklist_type
    # 0 = nothing
    # 1 = delete
    # 2 = warn
    # 3 = mute
    # 4 = kick
    # 5 = ban
    # 6 = tban
    # 7 = tmute
    with STICKSET_FILTER_INSERTION_LOCK:
        global CHAT_BLSTICK_BLACKLISTS
        curr_setting = SESSION.query(StickerSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = StickerSettings(
                chat_id, blacklist_type=int(blacklist_type), value=value)

        curr_setting.blacklist_type = int(blacklist_type)
        curr_setting.value = str(value)
        CHAT_BLSTICK_BLACKLISTS[str(chat_id)] = {
            "blacklist_type": int(blacklist_type),
            "value": value,
        }

        SESSION.add(curr_setting)
        SESSION.commit()


def get_blacklist_setting(chat_id):
    try:
        setting = CHAT_BLSTICK_BLACKLISTS.get(str(chat_id))
        if setting:
            return setting["blacklist_type"], setting["value"]
        else:
            return 1, "0"

    finally:
        SESSION.close()


def __load_CHAT_STICKERS():
    global CHAT_STICKERS
    try:
        chats = SESSION.query(StickersFilters.chat_id).distinct().all()
        for (chat_id,) in chats:  # remove tuple by ( ,)
            CHAT_STICKERS[chat_id] = []

        all_filters = SESSION.query(StickersFilters).all()
        for x in all_filters:
            CHAT_STICKERS[x.chat_id] += [x.trigger]

        CHAT_STICKERS = {x: set(y) for x, y in CHAT_STICKERS.items()}

    finally:
        SESSION.close()


def __load_chat_stickerset_blacklists():
    global CHAT_BLSTICK_BLACKLISTS
    try:
        chats_settings = SESSION.query(StickerSettings).all()
        for x in chats_settings:  # remove tuple by ( ,)
            CHAT_BLSTICK_BLACKLISTS[x.chat_id] = {
                "blacklist_type": x.blacklist_type,
                "value": x.value,
            }

    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with STICKERS_FILTER_INSERTION_LOCK:
        chat_filters = (
            SESSION.query(StickersFilters).filter(
                StickersFilters.chat_id == str(old_chat_id)).all())
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()


__load_CHAT_STICKERS()
__load_chat_stickerset_blacklists()
