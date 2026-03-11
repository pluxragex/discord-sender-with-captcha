# MCL_Old — Discord self-bot (ultra-fast channel opener)

> Production-grade asynchronous Discord automation focused on **minimum latency** when a channel becomes writable.
> Designed around a per-channel state machine, async task orchestration, and captcha solving (optional).

> [!WARNING]
> **Self-bots violate Discord ToS** and can lead to account termination.
> You run this at your own risk. This repo is for educational / internal automation purposes.

## What's unique?

This project is built for one job: **be one of the first to send** a message when a channel permission flips from:

`send_messages = False` → `send_messages = True`

Key goals:

- Fast reaction (no blocking I/O, background tasks, minimal work on hot path)
- Robustness (timeouts, retries, graceful task cleanup)
- Correctness (avoid duplicate captcha processing, handle race conditions)
- Maintainability (modular structure, clear separation of responsibilities)

## Core behavior

### 1) Channel open event

Listens for `on_guild_channel_update`.

When permissions change from **cannot send** → **can send**, the bot immediately:

- checks last messages for captcha image (lookback window, default 300s)
- if found: solves captcha and sends `<message>\n<captcha_text>`
- if not found: sends base message(s) and starts real-time monitoring

### 2) Captcha before opening (history scan)

On channel open:

- read recent history (limit 50 messages)
- filter messages created within last `HISTORY_LOOKBACK_SECONDS`
- find supported image attachments: `png`, `jpg`, `jpeg`, `webp`
- if multiple: uses the most recent
- downloads image asynchronously and calls captcha API

### 3) Captcha after opening (real-time monitoring)

After sending base messages (when no captcha was found initially), the bot monitors the channel via `on_message`.

If an image attachment appears:

- solve it once
- send another sequence of messages with appended captcha text
- never process the same captcha message twice

### 4) Channel close event

When permissions flip back to `send_messages = False`:

- stop monitoring
- cancel all per-channel background tasks
- cleanup channel session state

## Message formats (from `.env`)