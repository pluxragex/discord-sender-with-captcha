from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import discord

from ..config import AppConfig
from ..logger import get_logger
from ..utils.image_utils import any_supported_attachment

logger = get_logger(__name__)


@dataclass
class HistoryScanner:
    config: AppConfig

    async def find_latest_captcha_message(
        self,
        channel: discord.TextChannel,
    ) -> Optional[Tuple[discord.Message, discord.Attachment]]:
        lookback_seconds = self.config.history_lookback_seconds
        now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
        threshold = now - dt.timedelta(seconds=lookback_seconds)

        try:
            async for msg in channel.history(limit=50, oldest_first=False):
                if msg.created_at < threshold:
                    break
                attachment = self._pick_supported_attachment(msg.attachments)
                if attachment:
                    logger.debug(
                        "Found captcha in history (channel=%s, message=%s)",
                        channel.id,
                        msg.id,
                    )
                    return msg, attachment
        except discord.Forbidden:
            logger.warning("Forbidden to read history for channel %s", channel.id)
        except discord.HTTPException as exc:
            logger.error("HTTPException while reading history for channel %s: %s", channel.id, exc)
        except Exception as exc:
            logger.error("Unexpected error while reading history for channel %s: %s", channel.id, exc)
        return None

    @staticmethod
    def _pick_supported_attachment(
        attachments: Sequence[discord.Attachment],
    ) -> Optional[discord.Attachment]:
        if not attachments:
            return None
        names = [att.filename for att in attachments]
        if not any_supported_attachment(names):
            return None
        for att in attachments:
            if any_supported_attachment([att.filename]):
                return att
        return None

