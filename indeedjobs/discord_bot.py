import asyncio
from functools import wraps
import logging
import os

import discord
from discord.ext import tasks
from discord.ext.commands import Bot, Context
import discord.types
from dotenv import load_dotenv


class DiscordBot(Bot):

    def __init__(self) -> None:



        command_prefix = "!"
        description = "Testing"
        intents: discord.Intents = discord.Intents.default()
        intents.messages = True
        intents.reactions = True
        intents.message_content = True

        super().__init__(command_prefix, help_command=None, description=description, intents=intents)

        self.logger: logging.Logger = logging.getLogger(__name__)
        self.task_delay: int = 1
        self.kill = False

        self.config_channel: discord.TextChannel | None = None
        self.notif_channel: discord.TextChannel | None = None
        try:
            load_dotenv()
            self.token: str = os.getenv("TOKEN")
            self.config_channel_id: int = int(os.getenv("CONFIG_CHANNEL"))
            self.notif_channel_id: int = int(os.getenv("NOTIFICATIONS_CHANNEL"))
        except Exception as e:
            self.logger.exception(e)
            self.kill = True


    async def _killswitch_check(self) -> None:
        '''Asynchronous checking whether the close command has been sent. Closes the connection if True.'''

        if self.kill:
            if self.config_channel is not None:
                await self.config_channel.send("Closing application, see you later!")
            await self.close()


    async def check_jobs(self) -> None:
        pass


    async def _get_channels(self) -> None:
        '''Asynchronous getting required channels once client is ready.'''
    
        while self.config_channel is None and not self.kill:
            self.config_channel = self.get_channel(self.config_channel_id)
            if self.config_channel is None:
                self.logger.error("Could not get config channel. Retrying...")
                await asyncio.sleep(1)

        while self.notif_channel is None and not self.kill:
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
            if not ctx.channel.id == self.config_channel_id:
                return
            await self.config_channel.send("Test success!")


        @self.command()
        @exception_handler_async
        async def close(ctx: Context) -> None:
            if not ctx.channel.id == self.config_channel_id:
                return
            await self.close()


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
            

        @tasks.loop(seconds=self.task_delay)
        @exception_handler_async
        async def tasks_loop() -> None:

            await asyncio.gather(self._killswitch_check(), self.check_jobs())


        @self.event
        @exception_handler_async
        async def on_ready() -> None:
            
            self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
            await self._get_channels()
            message = await self.config_channel.send("Bot is live!")
            asyncio.gather(message.add_reaction("✅"), message.add_reaction("❌"))
            await tasks_loop.start()

        super().run(self.token)