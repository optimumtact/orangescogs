from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from print.models import PrintableMessage


class MessageHTMLRenderer:
    CSS = """@page { size: A4; margin: 15mm; }
body { font-family: sans-serif; background: #fff; color: #1f1f1f; }
.channel-header { font-size: 2rem; font-weight: 700; margin-bottom: 1rem; }
.messages { display: flex; flex-direction: column; gap: 1rem; }
.message { display: grid; grid-template-columns: 48px minmax(0, 1fr); gap: 12px; padding: 12px; border: 1px solid #d0d0d0; page-break-inside: avoid; }
.message.target-message { border-left: 5px solid #444; background: #f9f9f9; }
.avatar { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.avatar-wrap { text-align: center; }
.header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 6px; }
.author { font-weight: 700; }
.timestamp { color: #666; font-size: 0.8rem; }
.content { white-space: pre-wrap; line-height: 1.45; }
.poll, .forward-message { margin-top: 12px; padding: 10px 12px; border: 1px solid #d9d9d9; border-radius: 8px; background: #fafafa; }
.poll-header, .forward-label { font-size: 0.75rem; letter-spacing: 0.04em; text-transform: uppercase; color: #555; margin-bottom: 8px; font-weight: 700; }
.poll-question { font-weight: 700; margin-bottom: 8px; }
.poll-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.poll-option { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 6px 0; border-top: 1px solid #e7e7e7; }
.poll-option:first-child { border-top: none; }
.poll-option-label { white-space: pre-wrap; }
.poll-votes { color: #444; font-weight: 700; }
.poll-total { margin-top: 8px; color: #666; font-size: 0.82rem; }
.forward-body { white-space: pre-wrap; line-height: 1.45; }
.inline-image, .inline-media { display: block; max-width: min(100%, 460px); max-height: 460px; margin-top: 12px; border: 1px solid #d0d0d0; }
.print-footer { margin-top: 2rem; font-size: 0.8rem; color: #585858; }"""

    @staticmethod
    def _normalise_media_url(url: str) -> str:
        return (url or "").split("?", 1)[0].split("#", 1)[0].lower()

    @staticmethod
    def _media_kind_for_url(url: str) -> str | None:
        lowered = MessageHTMLRenderer._normalise_media_url(url)
        if not lowered.startswith(("http://", "https://")):
            return None

        image_extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".svg",
            ".avif",
            ".heic",
            ".heif",
            ".apng",
            ".ico",
        )
        video_extensions = (
            ".mp4",
            ".mov",
            ".m4v",
            ".webm",
            ".avi",
            ".mkv",
            ".mpeg",
            ".mpg",
            ".ogg",
        )
        if any(lowered.endswith(ext) for ext in image_extensions):
            return "image"
        if any(lowered.endswith(ext) for ext in video_extensions):
            return "video"
        return None

    @staticmethod
    def _is_supported_media_url(url: str) -> bool:
        lowered = MessageHTMLRenderer._normalise_media_url(url)
        if not lowered.startswith(("http://", "https://")):
            return False
        return MessageHTMLRenderer._media_kind_for_url(url) in {"image", "video"}

    @staticmethod
    def _is_supported_image_url(url: str) -> bool:
        return MessageHTMLRenderer._media_kind_for_url(url) == "image"

    @staticmethod
    def _is_supported_media(attachment) -> bool:
        mime = (getattr(attachment, "content_type", "") or "").lower()
        if mime in {
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/gif",
            "image/webp",
            "image/bmp",
            "image/x-bmp",
            "image/x-ms-bmp",
            "image/svg+xml",
            "image/avif",
            "image/heic",
            "image/heif",
            "image/apng",
            "image/x-icon",
            "image/vnd.microsoft.icon",
            "video/mp4",
            "video/quicktime",
            "video/webm",
            "video/x-msvideo",
            "video/mpeg",
            "video/ogg",
            "video/x-matroska",
        }:
            return True

        filename = (getattr(attachment, "filename", "") or "").lower()
        if not filename:
            return False

        supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".svg",
            ".avif",
            ".heic",
            ".heif",
            ".ico",
            ".apng",
            ".mp4",
            ".mov",
            ".m4v",
            ".webm",
            ".avi",
            ".mkv",
            ".mpeg",
            ".mpg",
            ".ogg",
        }
        return any(filename.endswith(ext) for ext in supported_extensions)

    @staticmethod
    def _is_supported_image(attachment) -> bool:
        return MessageHTMLRenderer._is_supported_media(attachment)

    @staticmethod
    def _format_timestamp(value: Any) -> str:
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d-%H-%M")
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
                    "%Y-%m-%d-%H-%M"
                )
            except ValueError:
                pass
        return str(value)

    @staticmethod
    def _render_inline_media(url: str) -> str:
        safe_url = html.escape(url, quote=True)
        if MessageHTMLRenderer._media_kind_for_url(url) == "video":
            return (
                f'<video class="inline-media" src="{safe_url}" controls muted playsinline '
                'preload="metadata"></video>'
            )
        return f'<img class="inline-image" src="{safe_url}" alt="attachment">'

    @staticmethod
    def _order_context_messages(before_messages, target_message, after_messages):
        ordered_before = sorted(before_messages, key=lambda msg: msg.created_at)
        ordered_after = sorted(after_messages, key=lambda msg: msg.created_at)
        return ordered_before + [target_message] + ordered_after

    @classmethod
    def _normalise_message(
        cls, message: Any, is_target: bool = False
    ) -> PrintableMessage:
        avatar_url = getattr(
            getattr(message.author, "display_avatar", None), "url", None
        )
        image_urls: list[str] = []
        for attachment in getattr(message, "attachments", []) or []:
            if not cls._is_supported_media(attachment):
                continue
            image_urls.append(attachment.url)

        for embed in getattr(message, "embeds", []) or []:
            for field_name in ("image", "thumbnail", "video"):
                media = getattr(embed, field_name, None)
                if media is None:
                    continue
                url = getattr(media, "url", None) or getattr(media, "proxy_url", None)
                if not url:
                    continue
                if cls._is_supported_media_url(url):
                    image_urls.append(url)

        seen_urls: set[str] = set()
        unique_image_urls: list[str] = []
        for url in image_urls:
            normalised = cls._normalise_media_url(url)
            if normalised in seen_urls:
                continue
            seen_urls.add(normalised)
            unique_image_urls.append(url)

        mention_map = {
            str(mention.id): getattr(mention, "name", str(mention.id))
            for mention in getattr(message, "mentions", []) or []
        }
        author_name = (
            getattr(message.author, "display_name", None)
            or getattr(message.author, "name", None)
            or "Unknown"
        )

        return PrintableMessage(
            id=message.id,
            author_name=author_name,
            author_avatar_url=avatar_url,
            timestamp=cls._format_timestamp(message.created_at),
            content=message.content or "",
            image_urls=unique_image_urls,
            mention_map=mention_map,
            poll=cls._extract_poll_data(message),
            forward=cls._extract_forward_data(message),
            is_target=is_target,
        )

    @staticmethod
    def _extract_poll_data(message: Any) -> dict[str, Any] | None:
        poll = getattr(message, "poll", None)
        if poll is None:
            return None

        question = getattr(poll, "question", "") or ""
        answers: list[dict[str, Any]] = []
        for answer in getattr(poll, "answers", []) or []:
            if answer is None:
                continue
            text = getattr(answer, "text", "") or ""
            emoji = getattr(answer, "emoji", None)
            answers.append(
                {
                    "text": text,
                    "emoji": str(emoji) if emoji is not None else "",
                    "vote_count": int(getattr(answer, "vote_count", 0) or 0),
                }
            )

        is_finalized = bool(getattr(poll, "is_finalized", lambda: False)())
        return {
            "question": question,
            "answers": answers,
            "total_votes": int(getattr(poll, "total_votes", 0) or 0),
            "is_finalized": is_finalized,
        }

    @staticmethod
    def _extract_forward_data(message: Any) -> dict[str, Any] | None:
        reference = getattr(message, "reference", None)
        if reference is None:
            return None

        ref_type = getattr(getattr(reference, "type", None), "value", None)
        if ref_type not in {1, None}:
            return None

        resolved = getattr(reference, "resolved", None)
        snapshot = None
        snapshots = getattr(message, "message_snapshots", []) or []
        if snapshots:
            snapshot = snapshots[-1]

        source = resolved or snapshot
        if source is None:
            return None

        source_content = getattr(source, "content", "") or ""
        source_author_name = (
            getattr(getattr(source, "author", None), "display_name", None)
            or getattr(getattr(source, "author", None), "name", None)
            or "Unknown"
        )
        source_image_urls: list[str] = []
        for attachment in getattr(source, "attachments", []) or []:
            if MessageHTMLRenderer._is_supported_media(attachment):
                source_image_urls.append(attachment.url)
        for embed in getattr(source, "embeds", []) or []:
            for field_name in ("image", "thumbnail"):
                media = getattr(embed, field_name, None)
                if media is None:
                    continue
                url = getattr(media, "url", None)
                if url and MessageHTMLRenderer._is_supported_media_url(url):
                    source_image_urls.append(url)

        return {
            "author_name": source_author_name,
            "content": source_content,
            "image_urls": list(dict.fromkeys(source_image_urls)),
        }

    @staticmethod
    def _render_poll_block(poll: dict[str, Any] | None) -> str:
        if not poll:
            return ""

        question = html.escape(str(poll.get("question") or "Poll"), quote=False)
        answers = poll.get("answers") or []
        rows: list[str] = []
        for answer in answers:
            if not isinstance(answer, dict):
                continue
            label = str(answer.get("text") or "Option").strip() or "Option"
            emoji = str(answer.get("emoji") or "").strip()
            vote_count = int(answer.get("vote_count") or 0)
            label_html = html.escape(label, quote=False)
            if emoji:
                label_html = f"{html.escape(emoji, quote=False)} {label_html}"
            rows.append(
                f'<li class="poll-option"><span class="poll-option-label">{label_html}</span><span class="poll-votes">{vote_count}</span></li>'
            )

        status = "Final results" if poll.get("is_finalized") else "Poll"
        total_votes = int(poll.get("total_votes") or 0)
        rows_html = "".join(rows) if rows else "<li class=\"poll-option\"><span class=\"poll-option-label\">No answers available</span></li>"
        return (
            f'<div class="poll">'
            f'<div class="poll-header">{html.escape(status, quote=False)}</div>'
            f'<div class="poll-question">{question}</div>'
            f'<ul class="poll-list">{rows_html}</ul>'
            f'<div class="poll-total">{total_votes} votes</div>'
            "</div>"
        )

    @staticmethod
    def _render_forward_block(forward: dict[str, Any] | None) -> str:
        if not forward:
            return ""

        author_name = html.escape(str(forward.get("author_name") or "Unknown"), quote=False)
        content = str(forward.get("content") or "")
        content_html = message_content_to_html(content)
        images = "".join(
            MessageHTMLRenderer._render_inline_media(url)
            for url in list(dict.fromkeys(forward.get("image_urls") or []))
        )
        return (
            f'<div class="forward-message">'
            f'<div class="forward-label">Forwarded from {author_name}</div>'
            f'<div class="forward-body">{content_html or "<em>Forwarded message</em>"}</div>'
            f"{images}"
            "</div>"
        )

    @classmethod
    def render_context_document(
        cls,
        channel_name: str,
        before_messages: list[Any],
        target_message: Any,
        after_messages: list[Any],
    ) -> str:
        printable_messages = [
            cls._normalise_message(message, message.id == target_message.id)
            for message in cls._order_context_messages(
                before_messages, target_message, after_messages
            )
            if not getattr(getattr(message, "author", None), "bot", False)
        ]
        return cls.render_document(channel_name, printable_messages)

    @classmethod
    def render_document(cls, channel_name: str, printable_messages: list[Any]) -> str:
        message_blocks: list[str] = []
        for message in printable_messages:
            avatar = ""
            author_avatar_url = getattr(message, "author_avatar_url", None)
            if author_avatar_url:
                avatar = (
                    f'<img class="avatar" src="{html.escape(author_avatar_url, quote=True)}" '
                    'alt="avatar">'
                )

            forward = getattr(message, "forward", None) or {}
            parent_image_urls = list(getattr(message, "image_urls", []) or [])
            forward_image_urls = list(dict.fromkeys(forward.get("image_urls") or []))
            unique_media_urls = list(
                dict.fromkeys(parent_image_urls + forward_image_urls)
            )
            seen_media_urls = {_normalise_media_url(url) for url in unique_media_urls}
            text = message_content_to_html(
                getattr(message, "content", ""),
                mentions=getattr(message, "mention_map", None),
                exclude_urls=seen_media_urls,
            )
            poll_html = cls._render_poll_block(getattr(message, "poll", None))
            filtered_forward = forward.copy()
            if forward_image_urls:
                filtered_forward["image_urls"] = [
                    url
                    for url in forward_image_urls
                    if url not in parent_image_urls
                ]
            forward_html = cls._render_forward_block(filtered_forward or None)
            images = "".join(cls._render_inline_media(url) for url in unique_media_urls)
            marker = " target-message" if getattr(message, "is_target", False) else ""
            message_blocks.append(
                f'<article class="message{marker}">'
                f'<div class="avatar-wrap">{avatar}</div>'
                '<div class="message-body">'
                f'<div class="header"><span class="author">{html.escape(getattr(message, "author_name", ""))}</span>'
                f'<span class="timestamp">{html.escape(cls._format_timestamp(getattr(message, "timestamp", "")))}</span></div>'
                f'<div class="content">{text}</div>'
                f"{poll_html}"
                f"{forward_html}"
                f"{images}"
                "</div>"
                "</article>"
            )

        return f"""<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>Discord Print</title>
  <style>{cls.CSS}</style>
</head>
<body>
  <header class=\"channel-header\"># {html.escape(channel_name)}</header>
  <main class=\"messages\">{''.join(message_blocks)}</main>
  <footer class=\"print-footer\">Printed from Discord</footer>
</body>
</html>"""


def _replace_mentions(text: str, mentions: dict[str, str] | None = None) -> str:
    if not text:
        return text
    if not mentions:
        return text

    def replace_token(match: re.Match[str]) -> str:
        user_id = match.group(1)
        username = mentions.get(user_id)
        if not username:
            return match.group(0)
        return f"@{username}"

    return re.sub(r"<@!?([0-9]+)>", replace_token, text)


def _normalise_media_url(url: str) -> str:
    return MessageHTMLRenderer._normalise_media_url(url)


def _media_kind_for_url(url: str) -> str | None:
    return MessageHTMLRenderer._media_kind_for_url(url)


def _render_media_tag(url: str) -> str:
    safe_url = html.escape(url, quote=True)
    kind = MessageHTMLRenderer._media_kind_for_url(url)
    if kind == "video":
        return (
            f'<video class="inline-media" src="{safe_url}" controls muted playsinline '
            'preload="metadata"></video>'
        )
    return f'<img class="inline-image" src="{safe_url}" alt="embedded media" />'


def message_content_to_html(
    content: str,
    mentions: dict[str, str] | None = None,
    exclude_urls: set[str] | None = None,
) -> str:
    if not content:
        return ""

    text = content.replace("\r\n", "\n").replace("\r", "\n")
    text = _replace_mentions(text, mentions)
    excluded = {_normalise_media_url(url) for url in (exclude_urls or set())}
    chunks: list[str] = []
    for segment in re.split(r"(https?://[^\s]+)", text):
        if not segment:
            continue
        if re.match(r"https?://[^\s]+", segment):
            if excluded and _normalise_media_url(segment) in excluded:
                safe_label = html.escape(segment, quote=True)
                chunks.append(safe_label)
                continue
            safe_url = html.escape(segment, quote=True)
            media_kind = _media_kind_for_url(segment)
            if media_kind == "image":
                chunks.append(_render_media_tag(segment))
                continue
            if media_kind == "video":
                chunks.append(_render_media_tag(segment))
                continue
            safe_label = html.escape(segment, quote=True)
            chunks.append(
                f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_label}</a>'
            )
        else:
            safe_text = html.escape(segment, quote=True).replace("\n", "<br>\n")
            chunks.append(safe_text)
    return "".join(chunks)
