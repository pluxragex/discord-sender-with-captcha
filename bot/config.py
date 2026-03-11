import os
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from dotenv import load_dotenv

from .logger import get_logger

logger = get_logger(__name__)

STATIC_GUILD_ID: Optional[int] = 1372832550502010930

@dataclass(frozen=True)
class ChannelConfig:
    channel_id: int
    messages: List[str]


@dataclass(frozen=True)
class AppConfig:
    bot_token: str
    captcha_api_token: str
    captcha_api_url: str
    channels: Dict[int, ChannelConfig]
    history_lookback_seconds: int = 300  # 5 minutes
    captcha_max_retries: int = 2
    captcha_request_timeout: float = 8.0  # seconds
    guild_id: int | None = None


def _normalize_text(msg: str) -> str:
    return msg.replace("\\n", "\n")


def _parse_message_value(raw: str) -> List[str]:
    raw = raw.strip()
    if not raw:
        return []

    if raw.startswith("[") and raw.endswith("]"):
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                result: List[str] = []
                for item in data:
                    if isinstance(item, str):
                        result.append(_normalize_text(item))
                    else:
                        result.append(_normalize_text(str(item)))
                return result
        except (json.JSONDecodeError, TypeError):
            pass

    return [_normalize_text(raw)]


def _parse_channel_messages(
    single: str | None, multiple: str | None
) -> List[str]:
    if multiple:
        if multiple.strip().startswith("["):
            parsed = _parse_message_value(multiple)
            if parsed:
                return parsed
        parts = [p.strip() for p in multiple.split("||") if p.strip()]
        if parts:
            return [_normalize_text(p) for p in parts]

    if single:
        parsed = _parse_message_value(single)
        if parsed:
            return parsed

    raise ValueError("Channel must define CHANNEL_X_MESSAGE or CHANNEL_X_MESSAGES")


def load_config() -> AppConfig:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")
    captcha_api_token = os.getenv("CAPTCHA_API_TOKEN")
    captcha_api_url = os.getenv("CAPTCHA_API_URL")

    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in environment")
    if not captcha_api_token:
        raise RuntimeError("CAPTCHA_API_TOKEN is not set in environment")
    if not captcha_api_url:
        raise RuntimeError("CAPTCHA_API_URL is not set in environment")

    channels_count_raw = os.getenv("CHANNELS_COUNT")
    if not channels_count_raw:
        raise RuntimeError("CHANNELS_COUNT is not set in environment")

    try:
        channels_count = int(channels_count_raw)
    except ValueError as exc:
        raise RuntimeError("CHANNELS_COUNT must be an integer") from exc

    channels: Dict[int, ChannelConfig] = {}
    for idx in range(1, channels_count + 1):
        prefix = f"CHANNEL_{idx}_"
        channel_id_raw = os.getenv(prefix + "ID")
        if not channel_id_raw:
            raise RuntimeError(f"{prefix}ID is not set in environment")
        try:
            channel_id = int(channel_id_raw)
        except ValueError as exc:
            raise RuntimeError(f"{prefix}ID must be an integer") from exc

        single_message = os.getenv(prefix + "MESSAGE")
        multiple_messages = os.getenv(prefix + "MESSAGES")

        messages = _parse_channel_messages(single_message, multiple_messages)

        channels[channel_id] = ChannelConfig(
            channel_id=channel_id,
            messages=messages,
        )

    logger.info("Loaded configuration for %d channels", len(channels))

    history_lookback_seconds = int(
        os.getenv("HISTORY_LOOKBACK_SECONDS", "300")
    )
    captcha_max_retries = int(os.getenv("CAPTCHA_MAX_RETRIES", "2"))
    captcha_request_timeout = float(
        os.getenv("CAPTCHA_REQUEST_TIMEOUT", "8.0")
    )

    return AppConfig(
        bot_token=bot_token,
        captcha_api_token=captcha_api_token,
        captcha_api_url=captcha_api_url,
        channels=channels,
        history_lookback_seconds=history_lookback_seconds,
        captcha_max_retries=captcha_max_retries,
        captcha_request_timeout=captcha_request_timeout,
        guild_id=STATIC_GUILD_ID,
    )

