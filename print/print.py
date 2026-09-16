from __future__ import annotations

import asyncio
import html
import io
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import discord

from redbot.core import Config, checks, commands

from .messages import MessageHTMLRenderer, message_content_to_html
from .models import PrintableMessage, PrintResult
from .printer import PrintApiClient, validate_print_service

log = logging.getLogger("red.oranges_print")
BaseCog = getattr(commands, "Cog", object)


class PrintCog(BaseCog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.config.register_guild(
            enabled=False,
            endpoint_url=None,
            token=None,
            threshold=5,
            current_threshold=5,
            last_print_at=None,
            last_threshold_update=None,
            escalation_window=900,
            reset_after=3600,
            max_threshold=100,
            threshold_step=5,
            max_print_jobs=2,
            rate_limit_window_seconds=300,
            rate_limit_notice_interval=120,
            last_rate_limit_warning=None,
            context_before=5,
            context_after=5,
            reaction="🖨️",
            printed_messages={},
            recent_print_jobs=[],
        )
        self._message_locks: dict[str, asyncio.Lock] = {}
        self._render_queue: asyncio.Queue[tuple[int, int, int]] = asyncio.Queue()
        self._render_worker_task = asyncio.create_task(self._render_worker())

    def cog_unload(self):
        self._render_worker_task.cancel()

    async def _render_worker(self):
        while True:
            try:
                guild_id, channel_id, message_id = await self._render_queue.get()
                try:
                    await self.print_discord_message(guild_id, channel_id, message_id)
                finally:
                    self._render_queue.task_done()
            except asyncio.CancelledError:
                break

    async def _get_lock(self, key: str) -> asyncio.Lock:
        lock = self._message_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._message_locks[key] = lock
        return lock

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        log.info(
            "Received reaction %s on message %s in channel %s of guild %s from user %s.",
            payload.emoji,
            payload.message_id,
            payload.channel_id,
            payload.guild_id,
            payload.user_id,
        )
        if payload.guild_id is None:
            return
        guild_cfg = self.config.guild_from_id(payload.guild_id)
        if not await guild_cfg.enabled():
            log.info(
                "Ignoring reaction for guild %s because print is disabled.",
                payload.guild_id,
            )
            return
        if payload.user_id == self.bot.user.id:
            log.info("Ignoring reaction from bot user %s.", payload.user_id)
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            log.info("Ignoring reaction for unknown guild %s.", payload.guild_id)
            return

        expected_reaction = await guild_cfg.reaction()
        if str(payload.emoji) != expected_reaction:
            log.info(
                "Reaction %s does not match configured reaction %s for guild %s.",
                payload.emoji,
                expected_reaction,
                payload.guild_id,
            )
            return

        user = guild.get_member(payload.user_id)
        if user is not None and user.bot:
            log.info(
                "Ignoring bot reaction from user %s in guild %s.",
                payload.user_id,
                payload.guild_id,
            )
            return

        log.info(
            "Matched print reaction %s on message %s in channel %s of guild %s; queueing print.",
            payload.emoji,
            payload.message_id,
            payload.channel_id,
            payload.guild_id,
        )
        await self._render_queue.put(
            (payload.guild_id, payload.channel_id, payload.message_id)
        )

    @staticmethod
    def _coerce_datetime(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _iter_recent_print_jobs(
        recent_print_jobs,
        now,
        window=timedelta(minutes=5),
    ) -> list[datetime]:
        timestamps: list[datetime] = []
        for value in recent_print_jobs or []:
            dt = PrintCog._coerce_datetime(value)
            if dt is None:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if now - dt <= window:
                timestamps.append(dt)
        return sorted(timestamps)

    @staticmethod
    def _is_print_allowed(
        recent_print_jobs,
        now,
        max_jobs=2,
        window=timedelta(minutes=5),
    ) -> tuple[bool, datetime | None]:
        recent_jobs = PrintCog._iter_recent_print_jobs(recent_print_jobs, now, window)
        if not recent_jobs:
            return True, None
        if len(recent_jobs) >= max_jobs:
            cooldown_until = min(recent_jobs) + window
            if now < cooldown_until:
                return False, cooldown_until
        return True, None

    @staticmethod
    def _calculate_required_threshold(
        base_threshold,
        current_threshold,
        last_print_at,
        last_threshold_update,
        now,
        reset_after=3600,
        escalation_window=900,
        max_threshold=5000,
    ):
        base_threshold = max(1, int(base_threshold or 1))
        current_threshold = max(
            base_threshold, int(current_threshold or base_threshold)
        )
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        last_print_dt = PrintCog._coerce_datetime(last_print_at)
        last_update_dt = PrintCog._coerce_datetime(last_threshold_update)
        if last_print_dt is not None and last_print_dt.tzinfo is None:
            last_print_dt = last_print_dt.replace(tzinfo=timezone.utc)
        if last_update_dt is not None and last_update_dt.tzinfo is None:
            last_update_dt = last_update_dt.replace(tzinfo=timezone.utc)

        if last_print_dt is not None and now - last_print_dt >= timedelta(
            seconds=reset_after
        ):
            return base_threshold
        if last_update_dt is not None and now - last_update_dt >= timedelta(
            seconds=escalation_window
        ):
            return base_threshold
        return min(max_threshold, max(base_threshold, current_threshold))

    @staticmethod
    def _calculate_next_threshold(
        base_threshold,
        current_threshold,
        max_threshold,
        threshold_step=5,
    ) -> int:
        base_threshold = max(1, int(base_threshold or 1))
        current_threshold = max(
            base_threshold, int(current_threshold or base_threshold)
        )
        step = max(1, int(threshold_step or 1))
        return min(max_threshold, max(base_threshold, current_threshold + step))

    @staticmethod
    def _should_warn_rate_limit(
        last_warning,
        now,
        interval_seconds=120,
    ) -> bool:
        if last_warning is None:
            return True
        last_warning_dt = PrintCog._coerce_datetime(last_warning)
        if last_warning_dt is None:
            return True
        if last_warning_dt.tzinfo is None:
            last_warning_dt = last_warning_dt.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now - last_warning_dt >= timedelta(seconds=interval_seconds)

    async def _get_effective_threshold(self, guild_cfg):
        base_threshold = await guild_cfg.threshold()
        current_threshold = await guild_cfg.current_threshold()
        last_print_at = await guild_cfg.last_print_at()
        last_threshold_update = await guild_cfg.last_threshold_update()
        reset_after = await guild_cfg.reset_after() or 3600
        escalation_window = await guild_cfg.escalation_window() or 900
        max_threshold = await guild_cfg.max_threshold() or 5000
        now = discord.utils.utcnow()

        effective_threshold = self._calculate_required_threshold(
            base_threshold,
            current_threshold,
            last_print_at,
            last_threshold_update,
            now,
            reset_after=reset_after,
            escalation_window=escalation_window,
            max_threshold=max_threshold,
        )

        if effective_threshold != current_threshold:
            await guild_cfg.current_threshold.set(effective_threshold)
        return effective_threshold

    async def _get_message_reactors(
        self, channel: discord.TextChannel, message_id: int, reaction: str
    ):
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return set()

        for reaction_obj in message.reactions:
            if str(reaction_obj.emoji) != reaction:
                continue
            users = []
            async for user in reaction_obj.users():
                if not user.bot:
                    users.append(user.id)
            return set(users)
        return set()

    async def _notify(self, channel: discord.TextChannel, message: str):
        try:
            await channel.send(message)
        except (discord.Forbidden, discord.HTTPException):
            log.warning(
                "Could not send status update for print event in %s", channel.id
            )

    async def print_discord_message(
        self, guild_id: int, channel_id: int, message_id: int
    ) -> PrintResult:
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return PrintResult(success=False, error="Guild not found.")

        guild_cfg = self.config.guild_from_id(guild_id)
        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return PrintResult(
                success=False, error="Channel not available or not a text channel."
            )

        reaction = await guild_cfg.reaction()
        threshold = await self._get_effective_threshold(guild_cfg)
        base_threshold = await guild_cfg.threshold() or 5
        if not base_threshold:
            base_threshold = 1

        lock = await self._get_lock(f"{guild_id}:{channel_id}:{message_id}")
        async with lock:
            data = await guild_cfg.printed_messages()
            key = f"{channel_id}:{message_id}"
            record = data.get(key)
            if record and record.get("status") in {"printed", "printing"}:
                return PrintResult(
                    success=False,
                    error="This message is already being processed or has been printed.",
                )

            unique_users = await self._get_message_reactors(
                channel, message_id, reaction
            )
            log.info(
                "Message %s in guild %s channel %s has %s unique reactors for reaction %s; threshold=%s (base=%s).",
                message_id,
                guild_id,
                channel_id,
                len(unique_users),
                reaction,
                threshold,
                base_threshold,
            )
            if len(unique_users) < threshold:
                log.info(
                    "Threshold not reached for message %s; skipping print.",
                    message_id,
                )
                return PrintResult(success=False, error="Threshold not reached.")

            now = discord.utils.utcnow()
            recent_jobs = await guild_cfg.recent_print_jobs()
            max_print_jobs = await guild_cfg.max_print_jobs() or 2
            rate_limit_window = await guild_cfg.rate_limit_window_seconds() or 300
            allowed, cooldown_until = self._is_print_allowed(
                recent_jobs,
                now,
                max_jobs=max_print_jobs,
                window=timedelta(seconds=rate_limit_window),
            )
            if not allowed:
                wait_seconds = max(0, int((cooldown_until - now).total_seconds()))
                log.info(
                    "Guild %s print rate limit reached; skipping print until %s (%s seconds remaining).",
                    guild_id,
                    cooldown_until.isoformat(),
                    wait_seconds,
                )
                if len(unique_users) >= threshold:
                    notice_interval = (
                        await guild_cfg.rate_limit_notice_interval() or 120
                    )
                    if self._should_warn_rate_limit(
                        await guild_cfg.last_rate_limit_warning(),
                        now,
                        interval_seconds=notice_interval,
                    ):
                        await self._notify(
                            channel,
                            "🖨️ Print votes are currently above the guild threshold, but the print rate limit is active. "
                            f"This will resume automatically in about {wait_seconds} seconds.",
                        )
                        await guild_cfg.last_rate_limit_warning.set(now.isoformat())
                return PrintResult(
                    success=False,
                    error=f"Print rate limit reached. Please wait {wait_seconds} seconds before printing again.",
                )

            data[key] = {
                "status": "printing",
                "updated_at": discord.utils.utcnow().isoformat(),
            }
            await guild_cfg.printed_messages.set(data)

            try:
                await self._notify(
                    channel,
                    f"🖨️ {len(unique_users)}/{threshold} print votes reached. Preparing print...",
                )
                result = await self._print_message_bundle(guild, channel, message_id)
                if result.success:
                    current_threshold = (
                        await guild_cfg.current_threshold() or base_threshold
                    )
                    threshold_step = await guild_cfg.threshold_step() or 5
                    next_threshold = self._calculate_next_threshold(
                        base_threshold,
                        current_threshold,
                        await guild_cfg.max_threshold() or 100,
                        threshold_step=threshold_step,
                    )
                    now = discord.utils.utcnow()
                    recent_jobs = self._iter_recent_print_jobs(
                        await guild_cfg.recent_print_jobs(), now
                    )
                    recent_jobs.append(now)
                    await guild_cfg.recent_print_jobs.set(
                        [job.isoformat() for job in recent_jobs]
                    )
                    await guild_cfg.current_threshold.set(next_threshold)
                    await guild_cfg.last_print_at.set(now.isoformat())
                    await guild_cfg.last_threshold_update.set(now.isoformat())
                    final_record = data.get(key, {})
                    final_record["status"] = "printed"
                    final_record["job_id"] = result.job_id
                    final_record["updated_at"] = now.isoformat()
                    data[key] = final_record
                    await guild_cfg.printed_messages.set(data)
                    await self._notify(
                        channel,
                        f"🖨️ Print job submitted to print service (job {result.job_id}). Required votes are now {next_threshold}.",
                    )
                else:
                    data.pop(key, None)
                    await guild_cfg.printed_messages.set(data)
                    await self._notify(
                        channel, "🖨️ Print failed: print service returned an error."
                    )
                return result
            except Exception as exc:  # pragma: no cover - runtime safety guard
                log.exception(
                    "Print pipeline failed for %s/%s/%s",
                    guild_id,
                    channel_id,
                    message_id,
                )
                data.pop(key, None)
                await guild_cfg.printed_messages.set(data)
                await self._notify(channel, "🖨️ Print failed: unexpected error.")
                return PrintResult(success=False, error=str(exc))

    async def _build_print_html_document(
        self, guild: discord.Guild, channel: discord.TextChannel, message_id: int
    ) -> tuple[str | None, str | None]:
        try:
            target_message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return None, "Target message was not found."

        guild_cfg = self.config.guild_from_id(guild.id)
        before_limit = await guild_cfg.context_before()
        after_limit = await guild_cfg.context_after()

        before_messages = [
            msg
            async for msg in channel.history(
                limit=before_limit, before=target_message, oldest_first=False
            )
        ]
        before_messages.reverse()
        after_messages = [
            msg
            async for msg in channel.history(
                limit=after_limit, after=target_message, oldest_first=True
            )
        ]

        return (
            MessageHTMLRenderer.render_context_document(
                channel.name,
                before_messages,
                target_message,
                after_messages,
            ),
            None,
        )

    async def _print_message_bundle(
        self, guild: discord.Guild, channel: discord.TextChannel, message_id: int
    ) -> PrintResult:
        guild_cfg = self.config.guild_from_id(guild.id)
        endpoint_url = await guild_cfg.endpoint_url()
        token = await guild_cfg.token()
        if not endpoint_url or not token:
            return PrintResult(
                success=False, error="Print API endpoint and token must be configured."
            )

        html_document, error = await self._build_print_html_document(
            guild, channel, message_id
        )
        if error or html_document is None:
            return PrintResult(success=False, error=error or "Failed to build HTML.")

        client = PrintApiClient(endpoint_url, token)
        return await client.submit_html(html_document)

    @staticmethod
    def _order_context_messages(before_messages, target_message, after_messages):
        ordered_before = sorted(before_messages, key=lambda msg: msg.created_at)
        ordered_after = sorted(after_messages, key=lambda msg: msg.created_at)
        return ordered_before + [target_message] + ordered_after

    @staticmethod
    def _render_document(
        channel_name: str, printable_messages: list[PrintableMessage]
    ) -> str:
        return MessageHTMLRenderer.render_document(channel_name, printable_messages)

    @commands.guild_only()
    @commands.group()
    async def print(self, ctx):
        """Discord print commands."""
        pass

    @commands.guild_only()
    @print.command(name="enable")
    @checks.mod_or_permissions(administrator=True)
    async def print_enable(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(True)
        await ctx.send("Discord Print enabled.")

    @commands.guild_only()
    @print.command(name="disable")
    @checks.mod_or_permissions(administrator=True)
    async def print_disable(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(False)
        await ctx.send("Discord Print disabled.")

    @commands.guild_only()
    @print.command(name="url")
    @checks.mod_or_permissions(administrator=True)
    async def print_url(self, ctx, url: str):
        await self.config.guild(ctx.guild).endpoint_url.set(url)
        await ctx.send(f"Print service URL set to {url}.")

    @commands.guild_only()
    @print.command(name="token")
    @checks.mod_or_permissions(administrator=True)
    async def print_token(self, ctx, token: str):
        await self.config.guild(ctx.guild).token.set(token)
        await ctx.send("Print service token configured.")

    @commands.guild_only()
    @print.command(name="threshold")
    @checks.mod_or_permissions(administrator=True)
    async def print_threshold(
        self,
        ctx,
        threshold: int,
        escalation_window: int = 900,
        reset_after: int = 3600,
        max_threshold: int = 100,
        step: int = 5,
    ):
        if threshold < 1:
            await ctx.send("Threshold must be at least 1.")
            return
        if escalation_window < 1:
            await ctx.send("Escalation window must be at least 1 second.")
            return
        if reset_after < 1:
            await ctx.send("Reset window must be at least 1 second.")
            return
        if step < 1:
            await ctx.send("Threshold step must be at least 1.")
            return
        if max_threshold < threshold:
            await ctx.send(
                "Maximum threshold must be greater than or equal to the base threshold."
            )
            return
        guild_cfg = self.config.guild(ctx.guild)
        await guild_cfg.threshold.set(threshold)
        await guild_cfg.current_threshold.set(threshold)
        await guild_cfg.escalation_window.set(escalation_window)
        await guild_cfg.reset_after.set(reset_after)
        await guild_cfg.max_threshold.set(max_threshold)
        await guild_cfg.threshold_step.set(step)
        await guild_cfg.last_print_at.set(None)
        await guild_cfg.last_threshold_update.set(None)
        await ctx.send(
            "Print thresholds configured:\n"
            f"Base threshold: {threshold}\n"
            f"Escalation window: {escalation_window}s\n"
            f"Reset after inactivity: {reset_after}s\n"
            f"Max threshold: {max_threshold}\n"
            f"Step increase: +{step}"
        )

    @commands.guild_only()
    @print.command(name="limit")
    @checks.mod_or_permissions(administrator=True)
    async def print_limit(self, ctx, max_jobs: int, window_seconds: int = 300):
        if max_jobs < 1:
            await ctx.send("Maximum print jobs must be at least 1.")
            return
        if window_seconds < 1:
            await ctx.send("Rate-limit window must be at least 1 second.")
            return
        guild_cfg = self.config.guild(ctx.guild)
        await guild_cfg.max_print_jobs.set(max_jobs)
        await guild_cfg.rate_limit_window_seconds.set(window_seconds)
        await ctx.send(
            "Print rate limit configured:\n"
            f"Max jobs per window: {max_jobs}\n"
            f"Window: {window_seconds}s"
        )

    @commands.guild_only()
    @print.command(name="context")
    @checks.mod_or_permissions(administrator=True)
    async def print_context(self, ctx, before: int, after: int):
        if before < 0 or after < 0:
            await ctx.send("Before/after context values must be non-negative.")
            return
        await self.config.guild(ctx.guild).context_before.set(before)
        await self.config.guild(ctx.guild).context_after.set(after)
        await ctx.send(f"Context set to {before} before / {after} after.")

    @commands.guild_only()
    @print.command(name="reaction")
    @checks.mod_or_permissions(administrator=True)
    async def print_reaction(self, ctx, reaction: str):
        await self.config.guild(ctx.guild).reaction.set(reaction)
        await ctx.send(f"Print reaction set to {reaction}.")

    @commands.guild_only()
    @print.command(name="status")
    async def print_status(self, ctx):
        guild_cfg = self.config.guild(ctx.guild)
        enabled = await guild_cfg.enabled()
        endpoint_url = await guild_cfg.endpoint_url()
        token = await guild_cfg.token()
        threshold = await guild_cfg.threshold()
        current_threshold = await guild_cfg.current_threshold() or threshold
        effective_threshold = await self._get_effective_threshold(guild_cfg)
        before = await guild_cfg.context_before()
        after = await guild_cfg.context_after()
        reaction = await guild_cfg.reaction()
        threshold_step = await guild_cfg.threshold_step() or 5
        max_print_jobs = await guild_cfg.max_print_jobs() or 2
        rate_limit_window = await guild_cfg.rate_limit_window_seconds() or 300
        rate_limit_notice_interval = await guild_cfg.rate_limit_notice_interval() or 120
        service_status = "not configured"
        if endpoint_url:
            ok, message = await validate_print_service(endpoint_url)
            service_status = "available" if ok else "unavailable"
            if not ok:
                service_status = f"{service_status} ({message})"
        await ctx.send(
            "Discord Print\n"
            f"Enabled: {'yes' if enabled else 'no'}\n"
            f"Service: {endpoint_url or 'not configured'}\n"
            f"Token: {'configured' if token else 'not configured'}\n"
            f"Base threshold: {threshold}\n"
            f"Current threshold: {effective_threshold}\n"
            f"Threshold step: +{threshold_step}\n"
            f"Max print jobs / {rate_limit_window}s window: {max_print_jobs}\n"
            f"Rate-limit notice interval: {rate_limit_notice_interval}s\n"
            f"Context: {before} before / {after} after\n"
            f"Reaction: {reaction}\n"
            f"Print API: {service_status}"
        )

    @commands.guild_only()
    @print.command(name="preview")
    @checks.mod_or_permissions(administrator=True)
    async def print_preview(self, ctx, message_id: int):
        html_document, error = await self._build_print_html_document(
            ctx.guild, ctx.channel, message_id
        )
        if error or html_document is None:
            await ctx.send(
                f"🖨️ Preview failed: {error or 'unable to build HTML preview.'}"
            )
            return

        await ctx.send(
            f"🖨️ HTML preview for message {message_id} in #{ctx.channel.name}",
            file=discord.File(
                io.StringIO(html_document),
                filename=f"print-preview-{message_id}.html",
            ),
        )

    @commands.guild_only()
    @print.command(name="printnow")
    @checks.mod_or_permissions(administrator=True)
    async def print_now(self, ctx, message_id: int):
        guild_cfg = self.config.guild(ctx.guild)
        endpoint_url = await guild_cfg.endpoint_url()
        token = await guild_cfg.token()
        if not endpoint_url or not token:
            await ctx.send(
                "Set the print service URL and token before running an admin print."
            )
            return
        try:
            result = await self._print_message_bundle(
                ctx.guild, ctx.channel, message_id
            )
        except Exception as exc:  # pragma: no cover - runtime safety guard
            log.exception(
                "Admin print failed for %s/%s/%s",
                ctx.guild.id,
                ctx.channel.id,
                message_id,
            )
            await ctx.send(f"🖨️ Admin print failed: {exc}")
            return

        if result.success:
            now = discord.utils.utcnow()
            recent_jobs = self._iter_recent_print_jobs(
                await guild_cfg.recent_print_jobs(), now
            )
            recent_jobs.append(now)
            await guild_cfg.recent_print_jobs.set(
                [job.isoformat() for job in recent_jobs]
            )
            await ctx.send(
                f"🖨️ Admin print submitted for message {message_id} (job {result.job_id})."
            )
        else:
            await ctx.send(
                f"🖨️ Admin print failed: {result.error or 'print service returned an error.'}"
            )

    @commands.guild_only()
    @print.command(name="htmltest")
    @checks.mod_or_permissions(administrator=True)
    async def print_html_test(self, ctx):
        guild_cfg = self.config.guild(ctx.guild)
        endpoint_url = await guild_cfg.endpoint_url()
        token = await guild_cfg.token()
        if not endpoint_url or not token:
            await ctx.send(
                "Set the print service URL and token before running the HTML test."
            )
            return

        html_document = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Simple Print Test</title>
  <style>
    body {
      font-family: sans-serif;
      margin: 24mm;
      color: #111;
      background: #fff;
    }
    h1 {
      font-size: 26px;
      margin-bottom: 12px;
    }
    p {
      font-size: 16px;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <h1>Print API Check</h1>
  <p>This is a simple HTML document used to test the configured print service.</p>
  <p>If this prints successfully, the endpoint and token are working correctly.</p>
</body>
</html>"""

        result = await PrintApiClient(endpoint_url, token).submit_html(html_document)
        if result.success:
            await ctx.send(
                f"🖨️ Simple HTML test sent to print service (job {result.job_id})."
            )
        else:
            await ctx.send(
                f"🖨️ HTML test failed: {result.error or 'print service returned an error.'}"
            )

    @commands.guild_only()
    @print.command(name="test")
    @checks.mod_or_permissions(administrator=True)
    async def print_test(self, ctx):
        guild_cfg = self.config.guild(ctx.guild)
        endpoint_url = await guild_cfg.endpoint_url()
        token = await guild_cfg.token()
        if not endpoint_url or not token:
            await ctx.send(
                "Set the print service URL and token before running the test print."
            )
            return

        sample_message = PrintableMessage(
            id=1,
            author_name="Alice",
            author_avatar_url=None,
            timestamp="2026-09-16T10:42:00Z",
            content="This is a sample print test.\nIt should render as a PDF via the print service.",
            image_urls=[],
            is_target=True,
        )
        html_document = MessageHTMLRenderer.render_document("general", [sample_message])
        result = await PrintApiClient(endpoint_url, token).submit_html(html_document)
        if result.success:
            await ctx.send(
                f"🖨️ Sample HTML sent to print service (job {result.job_id})."
            )
        else:
            await ctx.send(
                f"🖨️ Test print failed: {result.error or 'print service returned an error.'}"
            )
