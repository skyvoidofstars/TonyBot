import os
from dotenv import load_dotenv
from bot import NewBot
from commands import load_all_commands

load_dotenv()

TOKEN = os.getenv('TOKEN')

bot = NewBot()  
load_all_commands(bot)

bot.run(TOKEN)