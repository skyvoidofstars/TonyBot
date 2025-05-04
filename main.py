import os
from dotenv import load_dotenv
from bot import NewBot
from commands import load_all_commands
from events import load_all_events

load_dotenv()

TOKEN = os.getenv('TOKEN')

bot = NewBot()
load_all_commands(bot)
load_all_events(bot)

bot.run(TOKEN)