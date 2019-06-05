import threading
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer, func, distinct

from tg_bot.modules.helper_funcs.msg_types import Types
from tg_bot.modules.sql import SESSION, BASE


class ChatAccessConnectionSettings(BASE):
    __tablename__ = "access_connection"
    chat_id = Column(String(14), primary_key=True)
    allow_connect_to_chat = Column(Boolean, default=True)

    def __init__(self, chat_id, allow_connect_to_chat):
        self.chat_id = str(chat_id)
        self.allow_connect_to_chat = str(allow_connect_to_chat)

    def __repr__(self):
        return "<Chat access settings ({}) is {}>".format(self.chat_id, self.allow_connect_to_chat)


class Connection(BASE):
    __tablename__ = "connection"
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14))
    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id) #Ensure String


class ConnectionHistory(BASE):
    __tablename__ = "connection_history"
    user_id = Column(Integer, primary_key=True)
    chat_id1 = Column(String(14))
    chat_id2 = Column(String(14))
    chat_id3 = Column(String(14))
    def __init__(self, user_id, chat_id1, chat_id2, chat_id3):
        self.user_id = user_id
        self.chat_id1 = str(chat_id1) #Ensure String
        self.chat_id2 = str(chat_id2) #Ensure String
        self.chat_id3 = str(chat_id3) #Ensure String

ChatAccessConnectionSettings.__table__.create(checkfirst=True)
Connection.__table__.create(checkfirst=True)

CHAT_ACCESS_LOCK = threading.RLock()
CONNECTION_INSERTION_LOCK = threading.RLock()


def allow_connect_to_chat(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(ChatAccessConnectionSettings).get(str(chat_id))
        if chat_setting:
            return chat_setting.allow_connect_to_chat
        return False
    finally:
        SESSION.close()
        

def set_allow_connect_to_chat(chat_id: Union[int, str], setting: bool):
    with CHAT_ACCESS_LOCK:
        chat_setting = SESSION.query(ChatAccessConnectionSettings).get(str(chat_id))
        if not chat_setting:
            chat_setting = ChatAccessConnectionSettings(chat_id, setting)

        chat_setting.allow_connect_to_chat = setting
        SESSION.add(chat_setting)
        SESSION.commit()


def connect(user_id, chat_id):
    with CONNECTION_INSERTION_LOCK:
        prev = SESSION.query(Connection).get((int(user_id)))
        if prev:
            SESSION.delete(prev)
        connect_to_chat = Connection(int(user_id), chat_id)
        SESSION.add(connect_to_chat)
        SESSION.commit()
        return True


def get_connected_chat(user_id):
    try:
        return SESSION.query(Connection).get((int(user_id)))
    finally:
        SESSION.close()


def curr_connection(chat_id):
    try:
        return SESSION.query(Connection).get((str(chat_id)))
    finally :
        SESSION.close()



def disconnect(user_id):
    with CONNECTION_INSERTION_LOCK:
        disconnect = SESSION.query(Connection).get((int(user_id)))
        if disconnect:
            SESSION.delete(disconnect)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False
