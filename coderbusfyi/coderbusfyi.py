import logging
import re
from collections import OrderedDict
from urllib.parse import quote, unquote

import discord
from redbot.core import Config, commands

from .github_client import GitHubResourcesClient
from .views import PendingRequestViewManager

BaseCog = getattr(commands, "Cog", object)
log = logging.getLogger("red.oranges_coderbusfyi")


class CoderBusFYI(BaseCog):
    DEFAULT_REPO_OWNER = "optimumtact"
    DEFAULT_REPO_NAME = "coderbusfyi"
    DEFAULT_BRANCH = "main"
    DEFAULT_RESOURCE_PATH = "resources.ini"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self,
            identifier=571982634075330107,
            force_registration=True,
        )
        self.config.register_global(
            github_token=None,
            repo_owner=self.DEFAULT_REPO_OWNER,
            repo_name=self.DEFAULT_REPO_NAME,
            default_branch=self.DEFAULT_BRANCH,
            resource_path=self.DEFAULT_RESOURCE_PATH,
            pending_requests=[],
        )
        self.config.register_guild(notification_channel_id=None)
        self.github = GitHubResourcesClient(
            bot=bot,
            config=self.config,
            default_repo_owner=self.DEFAULT_REPO_OWNER,
            default_repo_name=self.DEFAULT_REPO_NAME,
            default_branch=self.DEFAULT_BRANCH,
            default_resource_path=self.DEFAULT_RESOURCE_PATH,
        )
        self.view_manager = PendingRequestViewManager(bot, self)

    async def initialize(self):
        await self.view_manager.rehydrate_pending_request_views(
            await self._get_pending_requests()
        )

    @staticmethod
    def parse_ini_entries(raw: str):
        entries = []
        current_section = "General"
        current_entry = None

        for raw_line in raw.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].strip()
                current_entry = None
                continue

            if "=" in line:
                key, value = [part.strip() for part in line.split("=", 1)]
                current_entry = {
                    "section": current_section,
                    "title": key,
                    "url": "",
                    "description": "",
                }
                if " | " in value:
                    url, description = [part.strip() for part in value.split("|", 1)]
                    current_entry["url"] = url
                    current_entry["description"] = re.sub(r"\s+", " ", description)
                else:
                    current_entry["url"] = value
                entries.append(current_entry)
                continue

            if current_entry is not None:
                current_entry["description"] = re.sub(
                    r"\s+",
                    " ",
                    f"{current_entry['description']} {line}".strip(),
                )

        for entry in entries:
            entry["description"] = entry["description"].strip()

        return entries

    @staticmethod
    def entries_to_ini(entries):
        ordered_sections = OrderedDict()
        for item in entries:
            section_name = item.get("section", "General").strip() or "General"
            ordered_sections.setdefault(section_name, []).append(item)

        lines = []
        for section_name, section_items in ordered_sections.items():
            lines.append(f"[{section_name}]")
            for item in section_items:
                title = str(item.get("title", "")).strip()
                url = str(item.get("url", "")).strip()
                description = str(item.get("description", "")).strip()
                if title and url:
                    if description:
                        lines.append(f"{title} = {url} | {description}")
                    else:
                        lines.append(f"{title} = {url}")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def normalize_line(title: str, url: str, description: str) -> str:
        cleaned_description = re.sub(r"\s+", " ", str(description).strip())
        return f"{str(title).strip()} = {str(url).strip()} | {cleaned_description}"

    @staticmethod
    def find_entry_by_url(entries, url):
        target_url = str(url).strip()
        for item in entries:
            if str(item.get("url", "")).strip() == target_url:
                return item
        return None

    @staticmethod
    def find_entry_by_title(entries, title):
        target_title = str(title).strip()
        for item in entries:
            if str(item.get("title", "")).strip() == target_title:
                return item
        return None

    @staticmethod
    def find_pending_request_by_url(pending_requests, url):
        target_url = str(url).strip()
        for item in pending_requests:
            if str(item.get("url", "")).strip() == target_url:
                return item
        return None

    @staticmethod
    def collect_sections(raw_ini):
        sections = []
        for raw_line in str(raw_ini or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue
            if line.startswith("[") and line.endswith("]"):
                section_name = line[1:-1].strip()
                if section_name:
                    sections.append(section_name)
        return sections

    @staticmethod
    def _choice_name(title, url):
        raw = f"{str(title).strip()} - {str(url).strip()}".strip(" -")
        if not raw:
            return "(unnamed request)"
        if len(raw) <= 100:
            return raw
        return raw[:97] + "..."

    @staticmethod
    def build_resource_choices(raw_ini):
        entries = CoderBusFYI.parse_ini_entries(str(raw_ini or ""))
        choices = []
        for entry in entries:
            title = str(entry.get("title", "")).strip()
            url = str(entry.get("url", "")).strip()
            if not title or not url:
                continue
            choices.append(
                discord.app_commands.Choice(
                    name=CoderBusFYI._choice_name(title, url),
                    value=url,
                )
            )
        return choices

    @staticmethod
    def build_pending_request_choices(pending_requests):
        choices = []
        for request in pending_requests:
            title = str(request.get("title", "")).strip()
            url = str(request.get("url", "")).strip()
            if not title or not url:
                continue
            choices.append(
                discord.app_commands.Choice(
                    name=CoderBusFYI._choice_name(title, url),
                    value=url,
                )
            )
        return choices

    @staticmethod
    def build_pending_request_notice(request):
        request_type = str(request.get("type", "add")).strip().lower()
        title = str(request.get("title", "")).strip()
        url = str(request.get("url", "")).strip()
        description = str(request.get("description", "")).strip()
        section = str(request.get("section", "")).strip()
        requested_by = str(request.get("requested_by", "")).strip() or "a user"

        if request_type == "remove":
            if description:
                return (
                    f"🔔 Pending removal request from {requested_by}:\n"
                    f"URL: <{url}>\n"
                    f"Reason: {description}"
                )
            return f"🔔 Pending removal request from {requested_by}:\n" f"URL: <{url}>"

        if section:
            base = (
                f"🔔 Pending add request from {requested_by}:\n"
                f"Title: {title}\n"
                f"URL: <{url}>\n"
                f"Section: {section}"
            )
            if description:
                return f"{base}\nDescription: {description}"
            return base

        base = (
            f"🔔 Pending add request from {requested_by}:\n"
            f"Title: {title}\n"
            f"URL: <{url}>"
        )
        if description:
            return f"{base}\nDescription: {description}"
        return base

    @staticmethod
    def build_pending_request_action_custom_id(request, action: str):
        action_name = str(action).strip().lower()
        requested_by_id = str(
            request.get("requested_by_id") or request.get("requested_by_id", "0")
        ).strip()
        if requested_by_id in ("", "None", "0"):
            requested_by_id = "0"
        url = str(request.get("url", "")).strip()
        return f"{action_name}:{requested_by_id}:{quote(url, safe='')}"

    @staticmethod
    def build_pending_request_resolution_notice(request, action: str, actor):
        action_name = str(action).strip().lower()
        status = "accepted" if action_name == "approve" else "denied"
        status_icon = "✅" if action_name == "approve" else "🐝"
        actor_label = (
            getattr(actor, "mention", str(actor)) if actor is not None else "an admin"
        )
        base = CoderBusFYI.build_pending_request_notice(request)
        return f"{base}\n\n{status_icon} Request {status} by {actor_label}."

    @staticmethod
    def build_requester_resolution_notice(request, action: str, actor):
        action_name = str(action).strip().lower()
        status = "approved" if action_name == "approve" else "denied"
        actor_label = (
            getattr(actor, "mention", str(actor)) if actor is not None else "an admin"
        )
        request_type = str(request.get("type", "add")).strip().lower()
        title = str(request.get("title", "")).strip()
        url = str(request.get("url", "")).strip()

        if request_type == "remove":
            return f"Your remove request for {url} was {status} by {actor_label}."

        return f"Your add request for '{title}' ({url}) was {status} by {actor_label}."

    @staticmethod
    def _log_text(value):
        return re.sub(r"\s+", " ", str(value).strip())

    @staticmethod
    def _actor_label(actor):
        if actor is None:
            return "an admin"

        mention = getattr(actor, "mention", None)
        if mention:
            return str(mention)

        display_name = getattr(actor, "display_name", None) or getattr(
            actor, "name", None
        )
        actor_id = getattr(actor, "id", None)
        if display_name and actor_id is not None:
            return f"{display_name} ({actor_id})"
        if display_name:
            return str(display_name)
        if actor_id is not None:
            return str(actor_id)
        return str(actor)

    def _log_pending_request_created(self, request):
        request_type = str(request.get("type", "add")).strip().lower()
        requester = self._log_text(request.get("requested_by", "a user"))
        requester_id = self._log_text(request.get("requested_by_id", "unknown"))
        title = self._log_text(request.get("title", ""))
        url = self._log_text(request.get("url", ""))
        description = self._log_text(request.get("description", ""))
        section = self._log_text(request.get("section", ""))

        if request_type == "remove":
            message = (
                "Pending remove request created by %s (user_id=%s): url=%s reason=%s"
            )
            values = (requester, requester_id, url, description or "(none)")
        else:
            message = (
                "Pending add request created by %s (user_id=%s): title=%s url=%s section=%s description=%s"
            )
            values = (
                requester,
                requester_id,
                title,
                url,
                section or "(none)",
                description or "(none)",
            )

        log.info(message, *values)

    def _log_pending_request_resolution(self, request, action, actor, source):
        action_name = str(action).strip().lower()
        status = "approved" if action_name == "approve" else "denied"
        request_type = str(request.get("type", "add")).strip().lower()
        requester = self._log_text(request.get("requested_by", "a user"))
        requester_id = self._log_text(request.get("requested_by_id", "unknown"))
        title = self._log_text(request.get("title", ""))
        url = self._log_text(request.get("url", ""))
        description = self._log_text(request.get("description", ""))
        section = self._log_text(request.get("section", ""))

        if request_type == "remove":
            message = (
                "Pending remove request %s via %s by %s: url=%s reason=%s requested_by=%s (user_id=%s)"
            )
            values = (
                status,
                source,
                self._actor_label(actor),
                url,
                description or "(none)",
                requester,
                requester_id,
            )
        else:
            message = (
                "Pending add request %s via %s by %s: title=%s url=%s section=%s description=%s requested_by=%s (user_id=%s)"
            )
            values = (
                status,
                source,
                self._actor_label(actor),
                title,
                url,
                section or "(none)",
                description or "(none)",
                requester,
                requester_id,
            )

        log.info(message, *values)

    def _log_direct_admin_action(self, action, actor, **details):
        fields = []
        for key, value in details.items():
            if value is None:
                continue
            fields.append(f"{key}={self._log_text(value)}")
        payload = ", ".join(fields) if fields else "no details"
        log.info("Admin %s by %s: %s", action, self._actor_label(actor), payload)

    @staticmethod
    def parse_pending_request_action_custom_id(custom_id):
        if not custom_id:
            return None, None, None
        parts = str(custom_id).split(":", 2)
        if len(parts) != 3:
            return None, None, None
        action, requester_id, encoded_url = parts
        return action, requester_id, unquote(encoded_url)

    async def _get_notification_channel(self, guild):
        if guild is None:
            return None

        config = getattr(self, "config", None)
        if config is None:
            return None

        if isinstance(guild, int):
            guild_obj = self.bot.get_guild(guild)
        elif hasattr(guild, "id"):
            guild_obj = guild
        else:
            guild_obj = None

        if guild_obj is None or not hasattr(guild_obj, "id"):
            return None

        channel_id = await config.guild(guild_obj).notification_channel_id()
        if channel_id:
            channel = guild_obj.get_channel(channel_id)
            if channel is not None:
                return channel
        return None

    async def _get_owner_notification_target(self):
        owner_ids = set()
        owner_id = getattr(self.bot, "owner_id", None)
        if owner_id is not None:
            owner_ids.add(owner_id)
        for bot_owner_id in getattr(self.bot, "owner_ids", set()) or set():
            owner_ids.add(bot_owner_id)

        for owner_id in owner_ids:
            owner = self.bot.get_user(owner_id)
            if owner is None:
                try:
                    owner = await self.bot.fetch_user(owner_id)
                except Exception:
                    continue
            if owner is not None:
                return owner
        return None

    async def _notify_admins_pending_request(self, guild, request):
        channel = await self._get_notification_channel(guild)
        if channel is not None:
            try:
                message = await channel.send(
                    self.build_pending_request_notice(request),
                    view=self._build_pending_request_action_view(request),
                )
                await self._set_pending_request_message_id(request, message.id)
                return
            except Exception:
                pass

        owner = await self._get_owner_notification_target()
        if owner is None:
            return

        try:
            await owner.send(
                self.build_pending_request_notice(request),
                view=self._build_pending_request_action_view(request),
            )
        except Exception:
            return

    async def _notify_requester_resolution(self, request, action, actor):
        requester_id = request.get("requested_by_id")
        if requester_id is None:
            return

        try:
            requester_id = int(str(requester_id).strip())
        except (TypeError, ValueError):
            return

        requester = self.bot.get_user(requester_id)
        if requester is None:
            try:
                requester = await self.bot.fetch_user(requester_id)
            except Exception:
                return

        try:
            await requester.send(
                self.build_requester_resolution_notice(request, action, actor)
            )
        except Exception:
            return

    def _build_pending_request_action_view(self, request):
        return self.view_manager.build_pending_request_action_view(request)

    async def _set_pending_request_message_id(self, request, message_id):
        target_url = str(request.get("url", "")).strip()
        target_title = str(request.get("title", "")).strip()
        target_type = str(request.get("type", "add")).strip().lower()
        pending = await self._get_pending_requests()
        updated = False
        for item in pending:
            if (
                str(item.get("url", "")).strip() == target_url
                and str(item.get("title", "")).strip() == target_title
                and str(item.get("type", "add")).strip().lower() == target_type
            ):
                item["message_id"] = int(message_id)
                updated = True
                break
        if updated:
            await self._set_pending_requests(pending)

    async def _handle_pending_request_action(self, interaction, action, request):
        action_name = str(action).strip().lower()
        guild = interaction.guild
        requester_id = str(request.get("requested_by_id") or "").strip()
        url = str(request.get("url", "")).strip()

        if requester_id and str(interaction.user.id) != requester_id:
            can_manage = False
            if guild is not None:
                # Assume if user can see channel it's enough
                can_manage = True
            else:
                owner_ids = set()
                owner_id = getattr(self.bot, "owner_id", None)
                if owner_id is not None:
                    owner_ids.add(owner_id)
                for bot_owner_id in getattr(self.bot, "owner_ids", set()) or set():
                    owner_ids.add(bot_owner_id)
                can_manage = interaction.user.id in owner_ids
            if not can_manage:
                await interaction.response.send_message(
                    "Only the bot owner or a guild moderator can act on this request.",
                    ephemeral=True,
                )
                return

        pending = await self._get_pending_requests()
        request_to_update = self.find_pending_request_by_url(pending, url)
        if request_to_update is None:
            await interaction.response.send_message(
                "This request has already been handled or is no longer pending.",
                ephemeral=True,
            )
            return

        self._log_pending_request_resolution(
            request_to_update, action_name, interaction.user, "button"
        )

        if action_name == "deny":
            await self._remove_pending_request(
                title=request_to_update.get("title"), url=url
            )
            if interaction.message is not None:
                await interaction.message.edit(
                    content=self.build_pending_request_resolution_notice(
                        request_to_update,
                        "deny",
                        interaction.user,
                    ),
                    view=None,
                )
            await self._notify_requester_resolution(
                request_to_update, "deny", interaction.user
            )
            await interaction.response.defer()
            return

        if str(request_to_update.get("type", "add")).strip() == "remove":
            await self._apply_remove(url)
        else:
            await self._apply_add(
                str(request_to_update.get("title", "")).strip(),
                url,
                str(request_to_update.get("description", "")).strip(),
                str(request_to_update.get("section", "Toolbox")).strip() or "Toolbox",
            )

        await self._remove_pending_request(
            title=str(request_to_update.get("title", "")).strip(),
            url=url,
        )
        if interaction.message is not None:
            await interaction.message.edit(
                content=self.build_pending_request_resolution_notice(
                    request_to_update,
                    "approve",
                    interaction.user,
                ),
                view=None,
            )
        await self._notify_requester_resolution(
            request_to_update, "approve", interaction.user
        )
        await interaction.response.defer()

    @discord.app_commands.command(name="setnotificationchannel")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(
        channel="Channel where pending request notifications should be sent"
    )
    async def setnotificationchannel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        await self.config.guild(interaction.guild).notification_channel_id.set(
            channel.id
        )
        await interaction.response.send_message(
            f"✅ Pending request notifications will be sent to {channel.mention}.",
            ephemeral=True,
        )

    @discord.app_commands.command(name="clearnotificationchannel")
    @discord.app_commands.default_permissions(administrator=True)
    async def clearnotificationchannel(self, interaction: discord.Interaction):
        await self.config.guild(interaction.guild).notification_channel_id.set(None)
        await interaction.response.send_message(
            "✅ Pending request notifications will fall back to the bot owner when no channel is configured.",
            ephemeral=True,
        )

    async def _get_section_choices(
        self, current: str = ""
    ) -> list[discord.app_commands.Choice[str]]:
        try:
            content = await self.github.load_resources()
        except Exception:
            return []

        sections = self.collect_sections(content)
        if not sections:
            return []

        needle = (current or "").strip().lower()
        if needle:
            sections = [section for section in sections if needle in section.lower()]

        return [
            discord.app_commands.Choice(name=section, value=section)
            for section in sections[:25]
        ]

    async def _get_resource_choices(
        self, current: str = ""
    ) -> list[discord.app_commands.Choice[str]]:
        try:
            content = await self.github.load_resources()
        except Exception:
            return []

        choices = self.build_resource_choices(content)
        if not choices:
            return []

        needle = (current or "").strip().lower()
        if needle:
            choices = [
                choice
                for choice in choices
                if needle in choice.name.lower() or needle in choice.value.lower()
            ]
        return choices[:25]

    async def _get_pending_request_choices(
        self, current: str = ""
    ) -> list[discord.app_commands.Choice[str]]:
        pending = await self._get_pending_requests()
        choices = self.build_pending_request_choices(pending)
        if not choices:
            return []

        needle = (current or "").strip().lower()
        if needle:
            choices = [
                choice
                for choice in choices
                if needle in choice.name.lower() or needle in choice.value.lower()
            ]
        return choices[:25]

    async def _get_pending_requests(self):
        return await self.config.pending_requests() or []

    async def _set_pending_requests(self, pending):
        await self.config.pending_requests.set(pending)

    async def _pending_request_by_title(self, title):
        pending = await self._get_pending_requests()
        for item in pending:
            if str(item.get("title", "")).strip() == title.strip():
                return item
        return None

    async def _pending_request_by_url(self, url):
        pending = await self._get_pending_requests()
        for item in pending:
            if str(item.get("url", "")).strip() == str(url).strip():
                return item
        return None

    async def _append_pending_request(self, request):
        pending = await self._get_pending_requests()
        normalized = {
            "title": str(request["title"]).strip(),
            "url": str(request["url"]).strip(),
            "description": str(request.get("description", "")).strip(),
            "type": str(request.get("type", "add")).strip(),
            "section": str(request.get("section", "Toolbox")).strip(),
            "requested_by": str(request.get("requested_by", "")).strip(),
            "requested_by_id": str(request.get("requested_by_id", "")).strip(),
        }
        pending.append(normalized)
        await self._set_pending_requests(pending)
        return normalized

    async def _remove_pending_request(self, title=None, url=None):
        pending = await self._get_pending_requests()
        if title is not None and url is not None:
            pending = [
                item
                for item in pending
                if str(item.get("title", "")).strip() != str(title).strip()
                and str(item.get("url", "")).strip() != str(url).strip()
            ]
        elif title is not None:
            pending = [
                item
                for item in pending
                if str(item.get("title", "")).strip() != str(title).strip()
            ]
        elif url is not None:
            pending = [
                item
                for item in pending
                if str(item.get("url", "")).strip() != str(url).strip()
            ]
        await self._set_pending_requests(pending)

    async def _apply_add(self, title, url, description, section="Toolbox"):
        content = await self.github.load_resources()
        entries = self.parse_ini_entries(content)
        available_sections = self.collect_sections(content)

        if (
            self.find_entry_by_title(entries, title) is not None
            or self.find_entry_by_url(entries, url) is not None
        ):
            raise ValueError(
                f"A resource with title '{title}' or URL '{url}' already exists."
            )

        section_name = section.strip() or "Toolbox"
        if available_sections and section_name not in available_sections:
            raise ValueError(
                f"Section '{section_name}' does not exist. Pick one of: {', '.join(available_sections)}"
            )

        entries.append(
            {
                "section": section_name,
                "title": title.strip(),
                "url": url.strip(),
                "description": re.sub(r"\s+", " ", description.strip()),
            }
        )

        updated = self.entries_to_ini(entries)
        await self.github.save_resources(updated)
        return updated

    async def _apply_remove(self, url):
        content = await self.github.load_resources()
        entries = self.parse_ini_entries(content)
        match = self.find_entry_by_url(entries, url)
        if match is None:
            raise ValueError(f"No resource exists with URL '{url}'.")

        filtered = [
            item
            for item in entries
            if str(item.get("url", "")).strip() != str(url).strip()
        ]
        updated = self.entries_to_ini(filtered)
        await self.github.save_resources(updated)
        return updated

    async def _apply_section_add(self, section_name):
        content = await self.github.load_resources()
        entries = self.parse_ini_entries(content)
        existing_sections = {str(item.get("section", "")).strip() for item in entries}
        normalized = section_name.strip()
        if not normalized:
            raise ValueError("Section name cannot be blank.")
        if normalized in existing_sections:
            raise ValueError(f"Section '{normalized}' already exists.")
        entries.append(
            {"section": normalized, "title": "", "url": "", "description": ""}
        )
        updated = self.entries_to_ini(entries)
        await self.github.save_resources(updated)
        return updated

    async def _apply_section_remove(self, section_name):
        content = await self.github.load_resources()
        entries = self.parse_ini_entries(content)
        target = section_name.strip()
        filtered = [
            item for item in entries if str(item.get("section", "")).strip() != target
        ]
        if len(filtered) == len(entries):
            raise ValueError(f"Section '{target}' does not exist.")
        updated = self.entries_to_ini(filtered)
        await self.github.save_resources(updated)
        return updated

    @commands.command(name="setgithubkey")
    @commands.is_owner()
    async def setgithubkey(self, ctx, token: str):
        """Set the GitHub API token used to modify resources.ini."""
        await self.config.github_token.set(token.strip())
        await ctx.send("✅ GitHub API token saved.")

    @discord.app_commands.command(name="setgithubkey")
    @discord.app_commands.describe(
        token="GitHub personal access token used to access the coderbusfyi repo"
    )
    async def slash_setgithubkey(self, interaction: discord.Interaction, token: str):
        await self.config.github_token.set(token.strip())
        await interaction.response.send_message(
            "✅ GitHub API token saved.", ephemeral=True
        )

    @discord.app_commands.guild_only()
    @discord.app_commands.command(name="addrequest")
    @discord.app_commands.describe(
        title="The title to add to coderbus.fyi",
        url="The coderbus.fyi URL",
        description="A short note about the coderbus.fyi entry",
        section="Existing section to add this item to on coderbus.fyi",
    )
    async def addrequest(
        self,
        interaction: discord.Interaction,
        title: str,
        url: str,
        description: str,
        section: str,
    ):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        content = await self.github.load_resources()
        available_sections = self.collect_sections(content)
        if not available_sections:
            await interaction.response.send_message(
                "No resource sections are available yet. Ask an admin to create one first.",
                ephemeral=True,
            )
            return

        normalized = section.strip()
        if normalized not in available_sections:
            await interaction.response.send_message(
                f"Section '{normalized}' is not valid. Choose one of: {', '.join(available_sections)}",
                ephemeral=True,
            )
            return

        pending = await self._get_pending_requests()
        existing = next(
            (
                item
                for item in pending
                if str(item.get("title", "")).strip() == title.strip()
            ),
            None,
        )
        if existing is not None:
            await interaction.response.send_message(
                f"A pending request for '{title}' already exists.", ephemeral=True
            )
            return

        request = {
            "title": title,
            "url": url,
            "description": description,
            "type": "add",
            "section": normalized,
            "requested_by": interaction.user.mention,
            "requested_by_id": interaction.user.id,
        }
        self._log_pending_request_created(request)
        await self._append_pending_request(request)
        await self._notify_admins_pending_request(interaction.guild, request)
        await interaction.response.send_message(
            f"✅ Add request queued for '{title}'. Admin approval will add it to the '{normalized}' section.",
            ephemeral=True,
        )

    @addrequest.autocomplete("section")
    async def addrequest_section_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        return await self._get_section_choices(current)

    @discord.app_commands.guild_only()
    @discord.app_commands.command(name="removerequest")
    @discord.app_commands.describe(
        url="The coderbus.fyi item to remove",
        reason="Why this resource should be removed",
    )
    async def removerequest(
        self, interaction: discord.Interaction, url: str, reason: str
    ):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        await interaction.response.defer(ephemeral=True)

        normalized_reason = reason.strip()
        if not normalized_reason:
            await interaction.followup.send(
                "A removal reason is required.", ephemeral=True
            )
            return

        pending = await self._get_pending_requests()
        existing = next(
            (
                item
                for item in pending
                if str(item.get("url", "")).strip() == url.strip()
                and str(item.get("type", "")).strip() == "remove"
            ),
            None,
        )
        if existing is not None:
            await interaction.followup.send(
                f"A pending remove request for '{url}' already exists.", ephemeral=True
            )
            return

        request = {
            "title": url,
            "url": url,
            "description": normalized_reason,
            "type": "remove",
            "section": "Toolbox",
            "requested_by": interaction.user.mention,
            "requested_by_id": interaction.user.id,
        }
        self._log_pending_request_created(request)
        await self._append_pending_request(request)
        await self._notify_admins_pending_request(interaction.guild, request)
        await interaction.followup.send(
            f"✅ Remove request queued for '{url}'.", ephemeral=True
        )

    @removerequest.autocomplete("url")
    async def removerequest_url_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        return await self._get_resource_choices(current)

    @discord.app_commands.command(name="approverequest")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(url="The pending request to approve")
    async def approverequest(self, interaction: discord.Interaction, url: str):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        pending = await self._get_pending_requests()
        request = self.find_pending_request_by_url(pending, url)
        if request is None:
            await interaction.response.send_message(
                f"No pending request for URL '{url}' was found.", ephemeral=True
            )
            return

        self._log_pending_request_resolution(request, "approve", interaction.user, "command")

        try:
            if str(request.get("type", "add")).strip() == "remove":
                await self._apply_remove(str(request.get("url", "")).strip())
                message = f"✅ Removed resource '{request.get('url')}' from the repo."
            else:
                await self._apply_add(
                    str(request.get("title", "")).strip(),
                    str(request.get("url", "")).strip(),
                    str(request.get("description", "")).strip(),
                    str(request.get("section", "Toolbox")).strip() or "Toolbox",
                )
                message = f"✅ Approved add request for '{request.get('title')}'."
            await self._remove_pending_request(
                title=str(request.get("title", "")).strip(),
                url=str(request.get("url", "")).strip(),
            )
            await self._notify_requester_resolution(
                request, "approve", interaction.user
            )
            await interaction.response.send_message(message, ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(
                f"Approval failed: {exc}", ephemeral=True
            )

    @approverequest.autocomplete("url")
    async def approverequest_url_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        return await self._get_pending_request_choices(current)

    @discord.app_commands.command(name="add")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(
        title="Name to add to coderbus.fyi",
        url="coderbus.fyi URL",
        description="Description for the coderbus.fyi entry",
        section="Section to place it in on coderbus.fyi",
    )
    async def direct_add(
        self,
        interaction: discord.Interaction,
        title: str,
        url: str,
        description: str,
        section: str = "Toolbox",
    ):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        try:
            await self._apply_add(title, url, description, section)
            self._log_direct_admin_action(
                "add item",
                interaction.user,
                title=title,
                url=url,
                description=description,
                section=section,
            )
            await interaction.response.send_message(
                f"✅ Added '{title}' to the '{section}' section.", ephemeral=True
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"Add failed: {exc}", ephemeral=True
            )

    @direct_add.autocomplete("section")
    async def direct_add_section_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        return await self._get_section_choices(current)

    @discord.app_commands.command(name="remove")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(url="The coderbus.fyi URL to remove")
    async def direct_remove(self, interaction: discord.Interaction, url: str):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        try:
            await self._apply_remove(url)
            self._log_direct_admin_action(
                "remove item",
                interaction.user,
                url=url,
            )
            await interaction.response.send_message(
                f"✅ Removed resource '{url}'.", ephemeral=True
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"Remove failed: {exc}", ephemeral=True
            )

    @discord.app_commands.command(name="addsection")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(name="The new section name, e.g. Toolbox or Tools")
    async def addsection(self, interaction: discord.Interaction, name: str):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        try:
            await self._apply_section_add(name)
            self._log_direct_admin_action(
                "add section",
                interaction.user,
                section=name,
            )
            await interaction.response.send_message(
                f"✅ Added section '{name}'.", ephemeral=True
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"Add section failed: {exc}", ephemeral=True
            )

    @discord.app_commands.command(name="removesection")
    @discord.app_commands.default_permissions(administrator=True)
    @discord.app_commands.describe(name="The section to remove")
    async def removesection(self, interaction: discord.Interaction, name: str):
        token = await self.github.require_token(interaction)
        if token is None:
            return

        try:
            await self._apply_section_remove(name)
            self._log_direct_admin_action(
                "remove section",
                interaction.user,
                section=name,
            )
            await interaction.response.send_message(
                f"✅ Removed section '{name}'.", ephemeral=True
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"Remove section failed: {exc}", ephemeral=True
            )

    @removesection.autocomplete("name")
    async def removesection_autocomplete(
        self, interaction: discord.Interaction, current: str
    ):
        return await self._get_section_choices(current)

    async def red_delete_data_for_user(self, **kwargs):
        return
