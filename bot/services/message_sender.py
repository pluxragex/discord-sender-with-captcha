from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import discord

from ..config import ChannelConfig
from ..logger import get_logger

logger = get_logger(__name__)


@dataclass
class MessageSender:
    async def send_sequence(
        self,
        channel: discord.TextChannel,
        config: ChannelConfig,
        *,
        append_text: Optional[str] = None,
        delay: float = 0.1,
    ) -> List[discord.Message]:
        sent_messages: List[discord.Message] = []
        base_messages: List[str] = [m for m in config.messages if m.strip()]
        if not base_messages:
            return sent_messages

        for idx, base in enumerate(base_messages, start=1):
            content = base
            if append_text:
                content = f"{content}\n{append_text}"

            try:
                msg = await channel.send(content)
                sent_messages.append(msg)
                logger.info(
                    "Sent message %s/%s to channel %s (id=%s)",
                    idx,
                    len(base_messages),
                    channel.name,
                    channel.id,
                )
            except discord.Forbidden:
                logger.warning(
                    "Forbidden to send message in channel %s", channel.id
                )
                break
            except discord.HTTPException as exc:
                logger.error(
                    "HTTPException sending message in channel %s: %s",
                    channel.id,
                    exc,
                )
            except Exception as exc:
                logger.error(
                    "Unexpected error sending message in channel %s: %s",
                    channel.id,
                    exc,
                )

            if idx < len(base_messages) and delay > 0:
                await asyncio.sleep(delay)

        return sent_messages
