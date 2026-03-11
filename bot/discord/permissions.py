from __future__ import annotations

from typing import Optional, Tuple

import discord

from ..logger import get_logger

logger = get_logger(__name__)


def can_send_messages(
    channel: discord.abc.GuildChannel,
    me: Optional[discord.abc.User],
) -> bool:
    if me is None:
        return False

    if not isinstance(channel, discord.abc.Messageable):
        return False

    if not hasattr(channel, "permissions_for"):
        return False

    try:
        guild_me = getattr(channel.guild, "me", None)
        subject = guild_me or me
        perms = channel.permissions_for(subject)  # type: ignore[no-untyped-call]
        return bool(getattr(perms, "send_messages", False))
    except Exception as exc:
        logger.error("Error checking permissions for channel %s: %s", channel.id, exc)
        return False


def send_permission_changed(
    before: discord.abc.GuildChannel,
    after: discord.abc.GuildChannel,
    me: Optional[discord.abc.User],
) -> Tuple[bool, bool]:
    before_allowed = can_send_messages(before, me)
    after_allowed = can_send_messages(after, me)
    return before_allowed, after_allowed

