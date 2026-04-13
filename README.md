# Discord Sender
> A high-speed asynchronous Discord automation bot that reacts to channel permission openings and sends configured messages with optional captcha solving.

> [!WARNING]
> This project behaves like a self-bot workflow.  
> Using self-bot automation may violate Discord Terms of Service and can result in account restrictions or bans.

## What's unique?
The bot is optimized for one critical scenario: detect when a locked channel becomes writable and respond in milliseconds with preconfigured messages.  
It combines permission-change tracking, history scanning, real-time monitoring, and captcha solving in one event-driven pipeline.

## What technologies are used?
> [!WARNING]
> Below are the key technologies and infrastructure dependencies of the project.

### Core stack
* **Python 3.11+**
* **aiohttp**
* **python-dotenv**
* **discord.py-based local package (`discord/`)**
* **asyncio**

### External integrations
* **Captcha API** (configured via `CAPTCHA_API_URL` and `CAPTCHA_API_TOKEN`)
* **Discord Gateway / API**

## Why this architecture?
The project is split into focused modules (`config`, `discord`, `services`, `utils`, `captcha`) so hot-path events stay lightweight and predictable.  
Per-channel orchestration and async task management reduce blocking operations, avoid duplicate captcha processing, and make runtime cleanup safe.

## How can I run it locally?

### 1) Clone repository
```bash
git clone https://github.com/pluxragex/discord-sender-with-captcha.git
cd discord-sender-with-captcha
```

### 2) Create virtual environment and install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment
```bash
cp .env.example .env
```

Fill required variables in `.env`:
- `BOT_TOKEN`
- `CAPTCHA_API_TOKEN`
- `CAPTCHA_API_URL`
- `CHANNELS_COUNT`, `CHANNEL_X_ID`, `CHANNEL_X_MESSAGE` or `CHANNEL_X_MESSAGES`

Optional runtime settings:
- `LOG_LEVEL`
- `HISTORY_LOOKBACK_SECONDS`
- `CAPTCHA_MAX_RETRIES`
- `CAPTCHA_REQUEST_TIMEOUT`

### 4) Run the bot
```bash
python main.py
```

## Available functionality

### Channel open/close automation
* Tracks `on_guild_channel_update` events
* Detects permission transition `send_messages: False -> True`
* Sends one or multiple configured messages per target channel
* Stops and cleans per-channel tasks when permissions close again

### Captcha flow
* Scans recent history for fresh image attachments (`png`, `jpg`, `jpeg`, `webp`)
* Solves captcha via external API before initial send when available
* Starts real-time monitor after opening if captcha was not found in history
* Avoids processing the same captcha message more than once

### Runtime reliability
* Asynchronous HTTP session sharing for external API requests
* Retry and timeout controls for captcha requests
* Structured logging with configurable log level
* Isolated services for history scan, message sending, and channel monitoring

## Project structure
```text
bot/
  captcha/                # captcha API client / solver logic
  config.py               # environment parsing and app config model
  discord/                # discord client integration and permission helpers
  services/               # monitor, history scanner, and message sender services
  utils/                  # async and image utility helpers
  logger.py               # logging setup
  main.py                 # runtime assembly and startup logic
main.py                   # root entry point
requirements.txt          # Python dependencies
.env.example              # environment template
```

## Notes
> [!NOTE]
> For stable local execution, ensure your Discord token, captcha service credentials, and channel IDs are valid before startup.  
> Keep sensitive values only in `.env`
