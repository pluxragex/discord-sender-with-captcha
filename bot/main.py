from __future__ import annotations

import asyncio

import aiohttp

from .captcha.solver import CaptchaSolver
from .config import AppConfig, load_config
from .discord.client import AppRuntime, create_client
from .logger import get_logger, setup_logging
from .services.channel_monitor import ChannelMonitor
from .services.history_scanner import HistoryScanner
from .services.message_sender import MessageSender

logger = get_logger(__name__)


async def create_runtime(config: AppConfig) -> tuple[AppRuntime, aiohttp.ClientSession]:
    session = aiohttp.ClientSession()

    captcha_solver = CaptchaSolver(
        session=session,
        api_url=config.captcha_api_url,
        api_token=config.captcha_api_token,
        request_timeout=config.captcha_request_timeout,
        max_retries=config.captcha_max_retries,
    )

    history_scanner = HistoryScanner(config=config)
    message_sender = MessageSender()
    channel_monitor = ChannelMonitor(
        config=config,
        history_scanner=history_scanner,
        message_sender=message_sender,
        captcha_solver=captcha_solver,
    )

    runtime = AppRuntime(
        config=config,
        captcha_solver=captcha_solver,
        history_scanner=history_scanner,
        message_sender=message_sender,
        channel_monitor=channel_monitor,
    )

    return runtime, session


async def run_bot() -> None:
    setup_logging()
    config = load_config()

    runtime, session = await create_runtime(config)

    client = None
    try:
        client = create_client(runtime)
        await client.start(config.bot_token)
    finally:
        if client is not None:
            await client.close()
        await session.close()


def main() -> None:
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()

