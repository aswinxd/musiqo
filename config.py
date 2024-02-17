from os import getenv

from dotenv import load_dotenv

load_dotenv()
que = {}
SESSION_NAME = getenv("SESSION_NAME", "BQBXF2DOuDBLqJokSx9T0MRqVty2J2NwS7XudqGxCdGD1LFkHSwr8qXvFKwf00z0BoD5_HQB-l6puUksVrtjSDPHdsDnrUamcRPKHs26O17Rw9S4TifU-MZkWFbKMm8JB6YoUN4WAtQVcqqDqlYOh-T9Ci1gcKJ9v2CCxXH6r2ipXPYSW9lL0u3-Dm7AbslDbPu5FIoWBlFqYhA9wMN23Ks54DTI7BOLnJ8FStGwB_e0-l2fJKxvp7TzV45VCQGZYNTDv_w7irg1G_98ukz7Udxb6g4D0Zd86IHSXTtwDZf_konX7uWrt6LMetYoSk4o6UenfKRrv55wofvRSOkpSMOEAAAAAZuXmKgA")
BOT_TOKEN = getenv("BOT_TOKEN", "1810353153:AAHLFmOhtT2rJF25SHvs4k6BScNJkp2P-6k")
BOT_NAME = getenv("BOT_NAME", "Musiqo")
admins = {}
API_ID = int(getenv("API_ID", "12799559"))
API_HASH = getenv("API_HASH", "077254e69d93d08357f25bb5f4504580")

DURATION_LIMIT = int(getenv("DURATION_LIMIT", "60"))

COMMAND_PREFIXES = list(getenv("COMMAND_PREFIXES", "/").split())

SUDO_USERS = list(map(int, getenv("SUDO_USERS").split()))
