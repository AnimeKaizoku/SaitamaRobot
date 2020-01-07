import threading

from sqlalchemy import Column, String, UnicodeText, func, distinct

from tg_bot.modules.helper_funcs.msg_types import Types
from tg_bot.modules.sql import SESSION, BASE

class GitHub(BASE):
    __tablename__ = "github"
    chat_id = Column(String(14), primary_key=True) #string because int is too large to be stored in a PSQL database.
    name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText, nullable=False)
    
    def __init__(self, chat_id, name, value):
        self.chat_id = str(chat_id)
        self.name = name
        self.value = value
    
    def __repr__(self):
        return "<Git Repo %s>" % self.name
        
GitHub.__table__.create(checkfirst=True)

GIT_LOCK = threading.RLock()

def add_repo_to_db(chat_id, name, value):
    with GIT_LOCK:
        prev = SESSION.query(GitHub).get((str(chat_id), name))
        if prev:
            SESSION.delete(prev)
        repo = GitHub(str(chat_id), name, value)
        SESSION.add(repo)
        SESSION.commit()
        
def get_repo(chat_id, name):
    try:
        return SESSION.query(GitHub).get((str(chat_id), name))
    finally:
        SESSION.close()
        
def rm_repo(chat_id, name):
    with GIT_LOCK:
        repo = SESSION.query(GitHub).get((str(chat_id), name))
        if repo:
            SESSION.delete(repo)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False

def get_all_repos(chat_id):
    try:
        return SESSION.query(GitHub).filter(GitHub.chat_id == str(chat_id)).order_by(GitHub.name.asc()).all()
    finally:
        SESSION.close()
        
