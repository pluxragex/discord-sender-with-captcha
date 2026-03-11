from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional, Set

import discord

from ..config import AppConfig, ChannelConfig
from ..logger import get_logger
from ..captcha.solver import CaptchaSolver
from .history_scanner import HistoryScanner
from .message_sender import MessageSender
from ..utils.image_utils import any_supported_attachment

logger = get_logger(__name__)


class ChannelState(Enum):
    IDLE = auto()
    OPEN = auto()
    WAITING_FOR_CAPTCHA = auto()
    CAPTCHA_SENT = auto()
    CLOSED = auto()


@dataclass
class ChannelSession:
    channel_id: int
    config: ChannelConfig
    state: ChannelState = ChannelState.IDLE
    last_captcha_message_id: Optional[int] = None
    active_tasks: Set[asyncio.Task] = field(default_factory=set)

    def track_task(self, task: asyncio.Task) -> None:
        self.active_tasks.add(task)

        def _done_callback(t: asyncio.Task) -> None:
            self.active_tasks.discard(t)

        task.add_done_callback(_done_callback)

    async def cancel_tasks(self) -> None:
        if not self.active_tasks:
            return
        for task in list(self.active_tasks):
            task.cancel()
        await asyncio.gather(*self.active_tasks, return_exceptions=True)
        self.active_tasks.clear()


@dataclass
class ChannelMonitor:
    config: AppConfig
    history_scanner: HistoryScanner
    message_sender: MessageSender
    captcha_solver: CaptchaSolver

    sessions: Dict[int, ChannelSession] = field(default_factory=dict)

    def get_or_create_session(self, channel_id: int) -> ChannelSession:
        if channel_id not in self.sessions:
            chan_cfg = self.config.channels.get(channel_id)
            if not chan_cfg:
                raise KeyError(f"Channel {channel_id} not configured")
            self.sessions[channel_id] = ChannelSession(
                channel_id=channel_id,
                config=chan_cfg,
            )
        return self.sessions[channel_id]

    async def on_channel_open(self, channel: discord.TextChannel) -> None:
        cfg_guild_id = self.config.guild_id
        if cfg_guild_id is not None and channel.guild.id != cfg_guild_id:
            return

        if channel.id not in self.config.channels:
            return

        session = self.get_or_create_session(channel.id)
        logger.info("Channel %s (%s) opened for sending", channel.id, channel.name)

        session.state = ChannelState.OPEN

        task = asyncio.create_task(self._handle_channel_open(channel, session))
        session.track_task(task)

    async def _handle_channel_open(
        self,
        channel: discord.TextChannel,
        session: ChannelSession,
    ) -> None:
        history_result = await self.history_scanner.find_latest_captcha_message(channel)
        if history_result:
            msg, attachment = history_result
            session.last_captcha_message_id = msg.id
            session.state = ChannelState.WAITING_FOR_CAPTCHA

            await self._solve_and_send_from_attachment(
                channel=channel,
                session=session,
                attachment=attachment,
                source_message_id=msg.id,
            )
            session.state = ChannelState.CAPTCHA_SENT
            return

        await self.message_sender.send_sequence(channel, session.config)
        session.state = ChannelState.WAITING_FOR_CAPTCHA

    async def on_channel_close(self, channel: discord.TextChannel) -> None:
        cfg_guild_id = self.config.guild_id
        if cfg_guild_id is not None and channel.guild.id != cfg_guild_id:
            return

        if channel.id not in self.config.channels:
            return

        session = self.get_or_create_session(channel.id)
        logger.info("Channel %s (%s) closed for sending", channel.id, channel.name)
        session.state = ChannelState.CLOSED
        await session.cancel_tasks()

    async def on_message(self, message: discord.Message) -> None:
        channel = message.channel
        if not isinstance(channel, discord.TextChannel):
            return

        cfg_guild_id = self.config.guild_id
        if cfg_guild_id is not None and channel.guild.id != cfg_guild_id:
            return

        if channel.id not in self.config.channels:
            return

        session = self.get_or_create_session(channel.id)
        if session.state not in {
            ChannelState.OPEN,
            ChannelState.WAITING_FOR_CAPTCHA,
        }:
            return

        if not message.attachments:
            return

        if session.last_captcha_message_id == message.id:
            return

        filenames = [att.filename for att in message.attachments]
        if not any_supported_attachment(filenames):
            return

        attachment = None
        for att in message.attachments:
            if any_supported_attachment([att.filename]):
                attachment = att
        if attachment is None:
            return

        session.last_captcha_message_id = message.id

        if session.state == ChannelState.CAPTCHA_SENT:
            return

        logger.debug(
            "New captcha message detected in channel=%s, message=%s",
            channel.id,
            message.id,
        )

        task = asyncio.create_task(
            self._solve_and_send_from_attachment(
                channel=channel,
                session=session,
                attachment=attachment,
                source_message_id=message.id,
            )
        )
        session.track_task(task)

    async def _solve_and_send_from_attachment(
        self,
        channel: discord.TextChannel,
        session: ChannelSession,
        attachment: discord.Attachment,
        source_message_id: int,
    ) -> None:
        captcha_text = await self.captcha_solver.solve_captcha_from_url(
            attachment.url,
            channel_id=channel.id,
            message_id=source_message_id,
        )
        if not captcha_text:
            logger.warning(
                "Captcha text not obtained for channel=%s, message=%s",
                channel.id,
                source_message_id,
            )
            return

        await self.message_sender.send_sequence(
            channel,
            session.config,
            append_text=captcha_text,
        )
        session.state = ChannelState.CAPTCHA_SENT

