"""Telegram bot agent.

Input:  ResumeData + list[ComparisonResult] + list[JobItem]
Output: sends Telegram message(s); returns TelegramNotification

Calls the Telegram Bot API directly (no third-party library needed).
Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env.

The agent formats a clean, scannable message with the top N jobs and
sends it. Can also be triggered on-demand when new jobs are discovered.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from models.schemas import (
    JobItem,
    ResumeData,
    TelegramNotification,
)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_JOBS_IN_MESSAGE = 5   # keep messages scannable


def _days_old(item: JobItem) -> str:
    age = item.supporting_data.get("posting_age_days")
    if age is None:
        return "unknown age"
    if age == 0:
        return "posted today"
    if age == 1:
        return "posted yesterday"
    return f"{age}d old"


def _format_message(resume: ResumeData, jobs: list[JobItem]) -> str:
    """Build a readable Telegram-safe (MarkdownV2 escaped) message."""
    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    top = jobs[:MAX_JOBS_IN_MESSAGE]

    lines: list[str] = [
        f"🔍 *Welstra Job Alert*",
        f"Candidate: {_esc(resume.full_name)}",
        f"Role target: {_esc(resume.current_role or 'Not set')}",
        f"Updated: {_esc(now)}",
        "",
        f"*Top {len(top)} matches:*",
    ]

    for i, job in enumerate(top, start=1):
        score_pct = f"{job.match_score:.0%}"
        flags = ", ".join(job.red_flags[:2]) if job.red_flags else "no red flags"
        link  = str(job.link_to_job)
        lines += [
            "",
            f"{i}\\. [{_esc(job.job_name)} @ {_esc(job.company)}]({link})",
            f"   Match: {score_pct} · {_esc(_days_old(job))}",
            f"   ⚠️ {_esc(flags)}" if job.red_flags else f"   ✅ No red flags",
        ]

    lines += [
        "",
        "_Reply to this bot to ask interview prep questions\\._",
    ]
    return "\n".join(lines)


def _esc(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    special = r"\_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{c}" if c in special else c for c in text)


class TelegramBotAgent:
    """Send job match notifications to a Telegram chat."""

    def __init__(
        self,
        bot_token: str | None = None,
        default_chat_id: str | None = None,
    ) -> None:
        self.bot_token      = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.default_chat_id = default_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    async def run(
        self,
        resume: ResumeData,
        job_items: list[JobItem],
        chat_id: str | None = None,
        investigation_id: str = "unknown",
    ) -> TelegramNotification:
        """
        Format and send the job alert. Returns a TelegramNotification
        regardless of whether the send succeeded (errors are logged, not raised,
        so the pipeline keeps running if Telegram is not configured).
        """
        target_chat = chat_id or self.default_chat_id
        top_jobs    = job_items[:MAX_JOBS_IN_MESSAGE]
        message_text = _format_message(resume, top_jobs)

        if self.bot_token and target_chat:
            await self._send(target_chat, message_text)
        else:
            print(
                "[TelegramBotAgent] Token or chat_id not configured — "
                "message not sent. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
            )

        return TelegramNotification(
            user_id=target_chat or "not_configured",
            investigation_id=investigation_id,
            top_jobs=top_jobs,
            message_text=message_text,
        )

    async def _send(self, chat_id: str, text: str) -> None:
        url = TELEGRAM_API.format(token=self.bot_token)
        payload = {
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                print(
                    f"[TelegramBotAgent] Send failed: {resp.status_code} — {resp.text}"
                )