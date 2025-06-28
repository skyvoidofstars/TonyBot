import discord
import asyncio
import time
from discord import ui
from discord.ext import commands
from datetime import datetime
from db import User, Seizure, SeizureRefund, _new_session
from sqlalchemy import func
from sqlalchemy.orm import Session
from utils.DatabaseFunctions import create_db_snapshot
from utils.ErrorReporting import log_and_notify
from utils.UserManager import get_or_create_user
from views.apreensao.functions import new_refund_message_content
from views.apreensao.RefundButtons import RefundButtonsView
from config import seizure_channel_id, refund_channel_id, seizure_value, brasilia_tz


def _update_seizure_status(status: str, refund_id: int, limit_date: datetime):
    session: Session = _new_session()
    seizure_list: list[Seizure] = (
        session.query(Seizure)
        .filter(Seizure.status == 'CRIADO', Seizure.created_at <= limit_date)
        .all()
    )

    for seizure in seizure_list:
        seizure.status = status
        seizure.refund_id = refund_id
    session.commit()


async def _update_seizure_messages(bot: commands.Bot, refund_id: int, refund_message: str):
    _session: Session = _new_session()
    _seizure_messages: list[tuple[int]] = (
        _session.query(Seizure.message_id)
        .filter(Seizure.refund_id == refund_id, Seizure.status == 'REEMBOLSADO')
        .order_by(Seizure.created_at)
        .all()
    )

    i_timer: float = time.monotonic()
    for _message in _seizure_messages:
        
        # Etapa 1 --> busca a mensagem
        while True:
            try:
                _fetched_message: discord.Message = await bot.get_channel(
                    seizure_channel_id
                ).fetch_message(_message[0])
                break
            except discord.RateLimited as e:
                print(f'[RATE LIMIT] Fomos limitados ao buscar a mensagem {_message[0]}. Esperando {e.retry_after:.2f} segundos.')
                await asyncio.sleep(e.retry_after)
            except Exception as e:
                print(f'[ERRO INESPERADO] ao buscar a mensagem {_message[0]}: {e}. Pulando.')
                _fetched_message = None
                break
            
        if not _fetched_message:
            continue
            
        _embed: discord.Embed = _fetched_message.embeds[0]
        _embed.color = discord.Color.green()
        _embed.add_field(
            name=f'Reembolso realizado <t:{int(datetime.now().timestamp())}:R>',
            value=refund_message
        )

        # Etapa 2 --> edita a mensagem
        while True:
            try:
                await _fetched_message.edit(embed=_embed, view=None)
                break
            except discord.RateLimited as e:
                print(f'[RATE LIMIT] Fomos limitados ao editar a mensagem {_message[0]}. Esperando {e.retry_after:.2f} segundos.')
                await asyncio.sleep(e.retry_after)
            except Exception as e: # Simplificado, já que a mensagem existe
                print(f'[ERRO INESPERADO] ao editar a mensagem {_message[0]}: {e}. Pulando reação.')
                break
        # Etapa 3 --> reage a mensagem        
        while True:
            try:
                await _fetched_message.add_reaction('✅')
                break
            except discord.RateLimited as e:
                print(f'[RATE LIMIT] Fomos limitados ao reagir na mensagem {_message[0]}. Esperando {e.retry_after:.2f} segundos.')
                await asyncio.sleep(e.retry_after)
            except Exception as e:
                print(f'[ERRO INESPERADO] ao reagir na mensagem {_message[0]}: {e}.')
                break
            
    total_duration = time.monotonic() - i_timer
    print("="*40)
    print(f"✅ Processo de atualização de mensagens concluído.")
    print(f"   - Mensagens na fila: {len(_seizure_messages)}")
    print(f"   - Tempo total de execução: {total_duration:.2f} segundos.")
    print(f"   - Média de tempo por mensagem: {total_duration / len(_seizure_messages):.2f} segundos.")
    print("="*40)

        
class ApproveRefundView(ui.View):
    def __init__(
        self, bot: commands.Bot, original_message: discord.Message, limit_date: datetime
    ):
        super().__init__(timeout=90)
        self.bot = bot
        self.original_message = original_message
        self.upper_limit_date = limit_date

    @ui.button(label='Cancelar', style=discord.ButtonStyle.danger)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await self.on_timeout()

    @ui.button(label='Publicar reembolsos', style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: ui.Button):
        try:
            refund_channel = self.bot.get_guild(interaction.guild_id).get_channel(
                refund_channel_id
            )
        except Exception as e:
            await log_and_notify(bot=self.bot, interaction=interaction, text=e)
            return

        await interaction.response.defer()

        bot_advice = await interaction.channel.send(
            content=f'{interaction.user.mention} Publicação iniciada, aguarde alguns segundos...'
        )

        await create_db_snapshot(bot=self.bot)
        
        user: User = get_or_create_user(discord_user=interaction.user)

        session: Session = _new_session()

        total_value: int = (
            session.query((func.count(Seizure.seizure_id) * seizure_value))
            .join(User, User.user_id == Seizure.user_id)
            .filter(
                Seizure.status == 'CRIADO', Seizure.created_at <= self.upper_limit_date
            )
            .order_by(User.user_character_name)
            .scalar()
        )

        new_refund: SeizureRefund = SeizureRefund(
            total_value=total_value,
            status='EM ANDAMENTO',
            created_by=user.user_id,
            created_at=datetime.now(brasilia_tz),
        )

        session.add(new_refund)
        session.commit()
        session.refresh(new_refund)

        _update_seizure_status(
            status='REEMBOLSADO',
            refund_id=new_refund.refund_id,
            limit_date=self.upper_limit_date,
        )

        message_content, message_embed = await new_refund_message_content(
            bot=self.bot,
            refund_id=new_refund.refund_id,
            upper_limit_date=self.upper_limit_date,
        )

        refund_message: discord.Message = await refund_channel.send(
            content=message_content,
            embed=message_embed,
            view=RefundButtonsView(bot=self.bot),
        )

        new_refund.message_id = refund_message.id
        session.commit()
        session.close()

        await bot_advice.edit(
            content= (
                f'Reembolsos publicados: {refund_message.jump_url}\n\n'
                'As mensagens de apreensões estão sendo atualizadas, podem ocorrer falhas...\n\n'
                'Deletando mensagem em 10 segundos...'
            ),
            delete_after=10,
        )
        
        await _update_seizure_messages(bot=self.bot, refund_id=new_refund.refund_id, refund_message=refund_message.jump_url)
        
        await interaction.message.delete(delay=10)
        await self.on_timeout()

    async def on_timeout(self):
        await self.original_message.edit(
            content=self.original_message.content, view=None
        )
        self.stop()
