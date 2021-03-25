import threading
from sqlalchemy import Column, String, Boolean, UnicodeText
from AstrakoBot.modules.sql import SESSION, BASE


class PrivateNotes(BASE):
    __tablename__ = "private_notes"
    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False)

    def __init__(self, chat_id, setting):
        self.chat_id = str(chat_id)  # Ensure String
        self.setting = str(setting)


PrivateNotes.__table__.create(checkfirst=True)

PRIVATE_NOTES_INSERTION_LOCK = threading.RLock()

def get_private_notes(chat_id) -> bool:
    try:
        private_notes = SESSION.query(PrivateNotes).get(str(chat_id))
        if private_notes:
            return private_notes.setting
        return False
    finally:
        SESSION.close()


def set_private_notes(chat_id, setting: bool):
    with PRIVATE_NOTES_INSERTION_LOCK:
        private_notes = SESSION.query(PrivateNotes).get(str(chat_id))
        if not private_notes:
            private_notes = PrivateNotes(str(chat_id), setting = setting)

        private_notes.setting = setting
        SESSION.add(private_notes)
        SESSION.commit()

