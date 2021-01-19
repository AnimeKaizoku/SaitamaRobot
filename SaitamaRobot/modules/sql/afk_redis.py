from SaitamaRobot import REDIS

# AFK
def is_user_afk(userid):
    rget = REDIS.get(f'is_afk_{userid}')
    if rget:
        return True
    else:
        return False


def start_afk(userid, reason):
    REDIS.set(f'is_afk_{userid}', reason)
    
def afk_reason(userid):
    return strb(REDIS.get(f'is_afk_{userid}'))

def end_afk(userid):
    REDIS.delete(f'is_afk_{userid}')
    return True

# Helpers
def strb(redis_string):
    return str(redis_string)
