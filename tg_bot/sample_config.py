# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
import json
import os

def get_user_list(config, key):
    with open('{}/tg_bot/{}'.format(os.getcwd(), config), 'r') as json_file:
        return json.load(json_file)[key]


# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
class Config(object):
    LOGGER = True

    # REQUIRED
    API_KEY = "YOUR BOT TOKEN HERE"
    OWNER_ID = "YOUR OWN ID HERE"  # If you dont know, run the bot and do /id in your private chat with it
    OWNER_USERNAME = "YOUR USERNAME HERE"  #Just write it without the @ ex "Sawada"
    SUPPORT_CHAT = "No Support Chat exists" # Your telegram support chat username, must have the "@" Example: @MyBotSupportGroupChat

    # RECOMMENDED
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'  # needed for any database modules
    MESSAGE_DUMP = None  # needed to make sure 'save from' messages persist
    GBAN_LOGS = None #Channel ID here with the hyphen like -123456789
    LOAD = []
    NO_LOAD = ['translation', 'rss', 'cleaner', 'feds']   
    WEBHOOK = False
    URL = None

    # OPTIONAL
    #ID Seperation format [1,2,3,4]
    SUDO_USERS = get_user_list('elevated_users.json', 'sudos')  # List of id's -  (not usernames) for users which have sudo access to the bot.
    DEV_USERS = get_user_list('elevated_users.json', 'devs')  # List of id's - (not usernames) for developers who will have the same perms as the owner
    SUPPORT_USERS = get_user_list('elevated_users.json', 'supports')  # List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    WHITELIST_USERS = get_user_list('elevated_users.json', 'whitelists')  # List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = True  #Delete commands that users dont have access to, like delete /ban if a non admin uses it.
    STRICT_GBAN = True
    WORKERS = 8  # Number of subthreads to use. Set as number of threads your processor uses
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'  # banhammer marie sticker
    ALLOW_EXCL = True  # Allow ! commands as well as / (Leave this to true so that blacklist can work)
    CASH_API_KEY = None # Get one from https://www.alphavantage.co/support/#api-key
    TIME_API_KEY = None # Get one from https://timezonedb.com/register
    AI_API_KEY = None # Coffeehouse chatbot api key, get one from https://coffeehouse.intellivoid.info/
    WALL_API = None # Get one from https://wall.alphacoders.com/api.php


class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
