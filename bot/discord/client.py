from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import discord
from discord.ext import commands

from ..captcha.solver import CaptchaSolver
from ..config import AppConfig
from ..logger import get_logger
from ..services.channel_monitor import ChannelMonitor
from ..services.history_scanner import HistoryScanner
from ..services.message_sender import MessageSender
from .permissions import send_permission_changed

logger = get_logger(__name__)


@dataclass
class AppRuntime:

    config: AppConfig
    captcha_solver: CaptchaSolver
    history_scanner: HistoryScanner
    message_sender: MessageSender
    channel_monitor: ChannelMonitor


class SelfbotClient(commands.Bot):

    def __init__(self, runtime: AppRuntime) -> None:
        super().__init__(
            command_prefix="!",
            self_bot=True,  # type: ignore[arg-type]
        )
        self.runtime = runtime

    async def on_ready(self) -> None:
        logger.info(
            "Logged in as %s (id=%s)",
            self.user,
            getattr(self.user, "id", "unknown"),
        )

    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ) -> None:
        if not isinstance(after, discord.TextChannel) or not isinstance(before, discord.TextChannel):
            return

        cfg_guild_id = self.runtime.config.guild_id
        if cfg_guild_id is not None and after.guild.id != cfg_guild_id:
            return

        before_can, after_can = send_permission_changed(before, after, self.user)

        if not before_can and after_can:
            asyncio.create_task(self.runtime.channel_monitor.on_channel_open(after))
        elif before_can and not after_can:
            asyncio.create_task(self.runtime.channel_monitor.on_channel_close(after))

    async def on_message(self, message: discord.Message) -> None:
        if self.user is not None and message.author.id == self.user.id:
            return

        await self.runtime.channel_monitor.on_message(message)
        await self.process_commands(message)

def create_client(runtime: AppRuntime) -> SelfbotClient:
    return SelfbotClient(runtime)

