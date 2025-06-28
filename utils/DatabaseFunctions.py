import os, discord
import shutil
from datetime import datetime
from discord.ext import commands
from config import log_channel, aux_db_channel

async def create_db_snapshot(bot: commands.Bot) -> None:
    
    try:
        os.makedirs('database_snapshots', exist_ok=True)
        
        snapshot_file: str = os.path.join(
            'database_snapshots',
            f'data_{datetime.now().strftime('%Y.%m.%d %H.%M.%S')}.db'
        )

        if os.path.exists('data.db'):
            shutil.copy2('data.db', snapshot_file)
            print(f'{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Database snapshot created: {snapshot_file}')
            await bot.get_channel(aux_db_channel).send(
                content = (
                    '<@&1024067238711525436>\n'
                    'Snapshot criada com sucesso.'
                ),
                file = discord.File(snapshot_file)
            )
    except Exception as e:
        await bot.get_channel(log_channel).send(
            content = (
                '<@&1024067238711525436>\n'
                'Falha ao criar snapshot de database'
            )
        )