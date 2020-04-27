import threading

from sqlalchemy import Column, String

from tg_bot.modules.sql import BASE, SESSION


class ChatbotChats(BASE):
    __tablename__ = "chatbot_chats"
    chat_id = Column(String(14), primary_key=True)
    ses_id = Column(String(70))
    expires = Column(String(15))
    
    def __init__(self, chat_id, ses_id, expires):
        self.chat_id = chat_id
        self.ses_id = ses_id
        self.expires = expires
        
        
ChatbotChats.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def is_chat(chat_id):
    try:
        chat = SESSION.query(ChatbotChats).get(str(chat_id))
        if chat:
            return True
        else:
            return False
    finally:
        SESSION.close()
        
        
def set_ses(chat_id, ses_id, expires):
    with INSERTION_LOCK:
        autochat = SESSION.query(ChatbotChats).get(str(chat_id))
        if not autochat:
            autochat = ChatbotChats(str(chat_id), str(ses_id), str(expires))
        else:
            autochat.ses_id = str(ses_id)
            autochat.expires = str(expires)
            
        SESSION.add(autochat)
        SESSION.commit()
            
            
def get_ses(chat_id):
    autochat = SESSION.query(ChatbotChats).get(str(chat_id))
    sesh = ""
    exp = ""
    if autochat:
        sesh = str(autochat.ses_id)
        exp = str(autochat.expires)
        
    SESSION.close()
    return sesh, exp
    
    
def rem_chat(chat_id):
    with INSERTION_LOCK:
        autochat = SESSION.query(ChatbotChats).get(str(chat_id))
        if autochat:
            SESSION.delete(autochat)
            
        SESSION.commit()


def get_all_chats():
    try:
        return SESSION.query(ChatbotChats.chat_id).all()
    finally:
        SESSION.close()
