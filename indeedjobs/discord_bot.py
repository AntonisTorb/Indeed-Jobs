import asyncio
from functools import wraps
import logging
import os
import re
import sqlite3

import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Context
import discord.types
from dotenv import load_dotenv

from .configuration import Config
from .database import IndeedDb
from .utils import DISCORD_HELP, regex_id


class DiscordBot(Bot):

    def __init__(self, config: Config, indeed_db: IndeedDb) -> None:
        '''Discord bot that notifies the user for new `Indeed` job postings and performs db actions.'''

        self.config = config
        self.indeed_db = indeed_db
        
        command_prefix = "!"
        description = "Indeed Job scraper, type `/help` in the config channel for some useful commands and interactions."
        intents: discord.Intents = discord.Intents.default()
        intents.messages = True
        intents.reactions = True
        intents.message_content = True

        super().__init__(command_prefix, help_command=None, description=description, intents=intents)

        self.logger: logging.Logger = logging.getLogger(__name__)

        self.config_channel: discord.TextChannel | None = None
        self.notif_channel: discord.TextChannel | None = None
        try:
            load_dotenv()
            self.token: str = os.getenv("TOKEN")
            self.config_channel_id: int = int(os.getenv("CONFIG_CHANNEL"))
            self.notif_channel_id: int = int(os.getenv("NOTIFICATIONS_CHANNEL"))
        except Exception as e:
            self.logger.exception(e)
            self.config.kill = True


    async def _get_channels(self) -> None:
        '''Asynchronous getting required channels once client is ready.'''
    
        while self.config_channel is None and not self.config.kill:
            self.config_channel = self.get_channel(self.config_channel_id)
            if self.config_channel is None:
                self.logger.error("Could not get config channel. Retrying...")
                await asyncio.sleep(1)

        while self.notif_channel is None and not self.config.kill:
            self.notif_channel = self.get_channel(self.notif_channel_id)
            if self.notif_channel is None:
                self.logger.error("Could not get notification channel. Retrying...")
                await asyncio.sleep(1)

    
    def run(self) -> None:

        def exception_handler_async(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    self.logger.exception(e)
            return wrapper
        

        @self.command()
        @exception_handler_async
        async def test(ctx: Context):
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            await msg.edit(content="Test success!")
            if not ctx.channel.id == self.config_channel_id:
                return
            #await self.config_channel.send("Test success!")


        @self.command()
        @exception_handler_async
        async def help(ctx: Context):
            if not ctx.channel.id == self.config_channel_id:
                return
            await ctx.send(DISCORD_HELP)

        
        @self.command()
        @exception_handler_async
        async def set(ctx: Context, field: str, value: str):
            if not ctx.message.reference or not ctx.channel.id == self.notif_channel_id:
                return
            if field not in ("applied", "response", "rejected", "job_offer"):
                await ctx.send("Wrong field name, please type `!help` for a list of acceptable names.", delete_after=30)
                await ctx.message.delete()
                return
            if value not in ("0", "1"):
                await ctx.send("Wrong value, please type `!help` for a list of acceptable values.", delete_after=30)
                await ctx.message.delete()
                return
            
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            job_id = re.findall(regex_id, msg)
            # print(job_id)
            
            while self.config.db_busy:
                asyncio.sleep(1)

            self.config.db_busy = True 
            con: sqlite3.Connection
            cur: sqlite3.Cursor
            con, cur = self.indeed_db.get_con_cur()
            try:
                cur.execute("UPDATE indeed_jobs SET ? = ? WHERE id = ?", (field, int(value), job_id))
            except Exception as e:
                raise e
            finally:
                cur.close()
                con.close()
                self.config.db_busy = False  

            await ctx.send(f'{field} updated to {value} for job with Id: {job_id}', delete_after=30)
            await ctx.message.delete()


        @self.command()
        @exception_handler_async
        async def close(ctx: Context) -> None:
            if not ctx.channel.id == self.config_channel_id:
                return
            self.config.kill = True


        @self.event
        @exception_handler_async
        async def on_raw_reaction_add(payload: discord.RawReactionActionEvent) -> None:

            # print(payload.emoji.name, payload.emoji.id)
            # if payload.channel_id != self.notif_channel_id:
            #     return
            message: discord.Message = await self.get_channel(payload.channel_id).fetch_message(payload.message_id)
            
            if payload.emoji.name == "✅" and payload.user_id != self.user.id:
                await message.channel.send("✅")
            elif payload.emoji.name == "❌" and payload.user_id != self.user.id:
                await message.delete()
            

        @tasks.loop(seconds=1)
        @exception_handler_async
        async def _kill_loop() -> None:

            if self.config.kill:
                if self.config_channel is not None:
                    await self.config_channel.send("Closing application, see you later!")
                await self.close()
            

        @tasks.loop(seconds=self.config.bot_delay_sec)
        @exception_handler_async
        async def _tasks_loop() -> None:
            '''Checks if new job postings are in the database and notifies the user.'''

            while self.config.db_busy:
                asyncio.sleep(1)

            if not self.config.new_jobs_in_db:
                return

            self.config.db_busy = True 
            con: sqlite3.Connection
            cur: sqlite3.Cursor
            con, cur = self.indeed_db.get_con_cur()

            try:
                new_jobs = cur.execute('SELECT id, url, job_title, employer, description FROM indeed_jobs WHERE notified = 0')
                for job in new_jobs:
                    text = '''**Id**: {}
**URL**: {}
**Title**: {}
**Employer**: {}
**Description**: {}'''.format(*job)
                    message = await self.notif_channel.send(text)
                    asyncio.gather(message.add_reaction("✅"), message.add_reaction("❌"))
                    cur.execute('UPDATE indeed_jobs SET notified = 1 WHERE id = ?', (job[0],))
                    con.commit()
            except Exception as e:
                raise e
            finally:
                cur.close()
                con.close()
                self.config.new_jobs_in_db = False
                self.config.db_busy = False  


        @self.event
        @exception_handler_async
        async def on_ready() -> None:
            
            self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
            await self._get_channels()
            message = await self.config_channel.send("Bot is live!")
            asyncio.gather(message.add_reaction("✅"), message.add_reaction("❌"))
            #asyncio.gather(_kill_loop.start(), _tasks_loop.start())

        super().run(self.token)