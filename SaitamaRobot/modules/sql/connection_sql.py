import threading
import time
from typing import Union

from sqlalchemy import Column, String, Boolean, UnicodeText, Integer

from SaitamaRobot.modules.sql import SESSION, BASE


class ChatAccessConnectionSettings(BASE):
    __tablename__ = "access_connection"
    chat_id = Column(String(14), primary_key=True)
    allow_connect_to_chat = Column(Boolean, default=True)

    def __init__(self, chat_id, allow_connect_to_chat):
        self.chat_id = str(chat_id)
        self.allow_connect_to_chat = str(allow_connect_to_chat)

    def __repr__(self):
        return "<Chat access settings ({}) is {}>".format(
            self.chat_id, self.allow_connect_to_chat)


class Connection(BASE):
    __tablename__ = "connection"
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14))

    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id)  # Ensure String


class ConnectionHistory(BASE):
    __tablename__ = "connection_history"
    user_id = Column(Integer, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText)
    conn_time = Column(Integer)

    def __init__(self, user_id, chat_id, chat_name, conn_time):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.chat_name = str(chat_name)
        self.conn_time = int(conn_time)

    def __repr__(self):
        return "<connection user {} history {}>".format(self.user_id,
                                                        self.chat_id)


ChatAccessConnectionSettings.__table__.create(checkfirst=True)
Connection.__table__.create(checkfirst=True)
ConnectionHistory.__table__.create(checkfirst=True)

CHAT_ACCESS_LOCK = threading.RLock()
CONNECTION_INSERTION_LOCK = threading.RLock()
CONNECTION_HISTORY_LOCK = threading.RLock()

HISTORY_CONNECT = {}


def allow_connect_to_chat(chat_id: Union[str, int]) -> bool:
    try:
        chat_setting = SESSION.query(ChatAccessConnectionSettings).get(
            str(chat_id))
        if chat_setting:
            return chat_setting.allow_connect_to_chat
        return False
    finally:
        SESSION.close()


def set_allow_connect_to_chat(chat_id: Union[int, str], setting: bool):
    with CHAT_ACCESS_LOCK:
        chat_setting = SESSION.query(ChatAccessConnectionSettings).get(
            str(chat_id))
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
    finally:
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


def add_history_conn(user_id, chat_id, chat_name):
    global HISTORY_CONNECT
    with CONNECTION_HISTORY_LOCK:
        conn_time = int(time.time())
        if HISTORY_CONNECT.get(int(user_id)):
            counting = (
                SESSION.query(ConnectionHistory.user_id).filter(
                    ConnectionHistory.user_id == str(user_id)).count())
            getchat_id = {}
            for x in HISTORY_CONNECT[int(user_id)]:
                getchat_id[HISTORY_CONNECT[int(user_id)][x]["chat_id"]] = x
            if chat_id in getchat_id:
                todeltime = getchat_id[str(chat_id)]
                delold = SESSION.query(ConnectionHistory).get(
                    (int(user_id), str(chat_id)))
                if delold:
                    SESSION.delete(delold)
                    HISTORY_CONNECT[int(user_id)].pop(todeltime)
            elif counting >= 5:
                todel = list(HISTORY_CONNECT[int(user_id)])
                todel.reverse()
                todel = todel[4:]
                for x in todel:
                    chat_old = HISTORY_CONNECT[int(user_id)][x]["chat_id"]
                    delold = SESSION.query(ConnectionHistory).get(
                        (int(user_id), str(chat_old)))
                    if delold:
                        SESSION.delete(delold)
                        HISTORY_CONNECT[int(user_id)].pop(x)
        else:
            HISTORY_CONNECT[int(user_id)] = {}
        delold = SESSION.query(ConnectionHistory).get(
            (int(user_id), str(chat_id)))
        if delold:
            SESSION.delete(delold)
        history = ConnectionHistory(
            int(user_id), str(chat_id), chat_name, conn_time)
        SESSION.add(history)
        SESSION.commit()
        HISTORY_CONNECT[int(user_id)][conn_time] = {
            "chat_name": chat_name,
            "chat_id": str(chat_id),
        }


def get_history_conn(user_id):
    if not HISTORY_CONNECT.get(int(user_id)):
        HISTORY_CONNECT[int(user_id)] = {}
    return HISTORY_CONNECT[int(user_id)]


def clear_history_conn(user_id):
    global HISTORY_CONNECT
    todel = list(HISTORY_CONNECT[int(user_id)])
    for x in todel:
        chat_old = HISTORY_CONNECT[int(user_id)][x]["chat_id"]
        delold = SESSION.query(ConnectionHistory).get(
            (int(user_id), str(chat_old)))
        if delold:
            SESSION.delete(delold)
            HISTORY_CONNECT[int(user_id)].pop(x)
    SESSION.commit()
    return True


def __load_user_history():
    global HISTORY_CONNECT
    try:
        qall = SESSION.query(ConnectionHistory).all()
        HISTORY_CONNECT = {}
        for x in qall:
            check = HISTORY_CONNECT.get(x.user_id)
            if check is None:
                HISTORY_CONNECT[x.user_id] = {}
            HISTORY_CONNECT[x.user_id][x.conn_time] = {
                "chat_name": x.chat_name,
                "chat_id": x.chat_id,
            }
    finally:
        SESSION.close()


__load_user_history()
