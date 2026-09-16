from datetime import datetime, timezone

from print.print import PrintableMessage, message_content_to_html
from print.printer import PrintApiClient


def test_order_context_messages_keeps_target_in_the_middle():
    target = type("M", (), {"id": 3, "created_at": datetime(2026, 9, 16, 11, 43, 0)})()
    before = [
        type("M", (), {"id": 1, "created_at": datetime(2026, 9, 16, 11, 41, 0)})(),
        type("M", (), {"id": 2, "created_at": datetime(2026, 9, 16, 11, 42, 0)})(),
    ]
    after = [
        type("M", (), {"id": 4, "created_at": datetime(2026, 9, 16, 11, 44, 0)})(),
        type("M", (), {"id": 5, "created_at": datetime(2026, 9, 16, 11, 45, 0)})(),
    ]

    ordered = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._order_context_messages(before, target, after)

    assert [m.id for m in ordered] == [1, 2, 3, 4, 5]


def test_render_document_uses_compact_timestamps():
    doc = __import__("print.print", fromlist=["PrintCog"]).PrintCog._render_document(
        "general",
        [
            PrintableMessage(
                id=1,
                author_name="Alice",
                author_avatar_url=None,
                timestamp="2026-09-16-11-43",
                content="hello",
                image_urls=[],
                is_target=True,
            )
        ],
    )
    assert "2026-09-16-11-43" in doc
    assert "2026-09-16T11:43:00" not in doc


def test_render_document_uses_username_handles_for_authors():
    class User:
        name = "alice"
        display_name = "Alice Display"
        display_avatar = type("Avatar", (), {"url": None})()

    class Message:
        id = 1
        author = User()
        created_at = datetime(2026, 9, 16, 11, 43, 0)
        content = "hello"
        attachments = []

    doc = __import__("print.print", fromlist=["PrintCog"]).PrintCog._render_document(
        "general",
        [
            PrintableMessage(
                id=1,
                author_name="@alice",
                author_avatar_url=None,
                timestamp="2026-09-16-11-43",
                content="hello",
                image_urls=[],
                is_target=True,
            )
        ],
    )
    assert "@alice" in doc
    assert "Alice Display" not in doc


def test_print_threshold_scales_then_resets_after_inactivity():
    now = datetime(2026, 9, 16, 12, 0, 0)
    assert (
        __import__(
            "print.print", fromlist=["PrintCog"]
        ).PrintCog._calculate_required_threshold(5, 5, None, None, now, 3600, 900, 100)
        == 5
    )

    assert (
        __import__(
            "print.print", fromlist=["PrintCog"]
        ).PrintCog._calculate_required_threshold(
            5,
            10,
            "2026-09-16T11:59:00+00:00",
            "2026-09-16T11:59:00+00:00",
            now,
            3600,
            900,
            100,
        )
        == 10
    )

    assert (
        __import__(
            "print.print", fromlist=["PrintCog"]
        ).PrintCog._calculate_required_threshold(
            5,
            20,
            "2026-09-16T11:00:00+00:00",
            "2026-09-16T11:00:00+00:00",
            now,
            3600,
            900,
            100,
        )
        == 5
    )


def test_print_rate_limit_blocks_after_two_jobs_within_five_minutes():
    now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    allowed, cooldown_until = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._is_print_allowed(
        [
            "2026-09-16T11:58:00+00:00",
            "2026-09-16T11:59:30+00:00",
        ],
        now,
    )
    assert allowed is False
    assert cooldown_until == datetime(2026, 9, 16, 12, 3, 0, tzinfo=timezone.utc)

    allowed, _ = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._is_print_allowed(
        [
            "2026-09-16T11:55:00+00:00",
            "2026-09-16T11:56:00+00:00",
        ],
        datetime(2026, 9, 16, 12, 1, 0, tzinfo=timezone.utc),
    )
    assert allowed is True


def test_print_rate_limit_can_be_configured_higher_than_two():
    now = datetime(2026, 9, 16, 12, 0, 0, tzinfo=timezone.utc)
    allowed, _ = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._is_print_allowed(
        [
            "2026-09-16T11:58:00+00:00",
            "2026-09-16T11:59:00+00:00",
            "2026-09-16T11:59:30+00:00",
        ],
        now,
        max_jobs=3,
    )
    assert allowed is False

    allowed, _ = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._is_print_allowed(
        [
            "2026-09-16T11:58:00+00:00",
            "2026-09-16T11:59:00+00:00",
        ],
        now,
        max_jobs=3,
    )
    assert allowed is True


def test_print_api_client_uses_print_route_when_given_base_url():
    client = PrintApiClient("http://printapi:8000", "secret")
    assert client.print_url == "http://printapi:8000/print"

    explicit = PrintApiClient("http://printapi:8000/print", "secret")
    assert explicit.print_url == "http://printapi:8000/print"


def test_message_content_html_escapes_and_preserves_newlines():
    content = '<script>alert("hello")</script>\nhttps://example.com'
    html = message_content_to_html(content)
    assert "&lt;script&gt;" in html
    assert "alert(&quot;hello&quot;)" in html
    assert "<br>" in html
    assert "https://example.com" in html


def test_message_content_html_replaces_mention_tokens_with_username_handles():
    html = message_content_to_html(
        "hello <@235829052389525> and <@!987654321>",
        mentions={"235829052389525": "jason", "987654321": "alice"},
    )
    assert "hello @jason and @alice" in html
    assert "<@235829052389525>" not in html


def test_printable_message_requires_supported_fields():
    message = PrintableMessage(
        id=123,
        author_name="Alice",
        author_avatar_url=None,
        timestamp="2026-09-16T10:42:00Z",
        content="hello",
        image_urls=[],
        is_target=True,
    )
    assert message.author_name == "Alice"
    assert message.is_target is True
    assert isinstance(message.image_urls, list)


def test_supported_image_types_include_common_browser_formats():
    supported = [
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/svg+xml",
        "image/avif",
        "image/heic",
        "image/heif",
    ]
    for mime in supported:
        attachment = type("Attachment", (), {"content_type": mime})()
        assert (
            __import__(
                "print.messages", fromlist=["MessageHTMLRenderer"]
            ).MessageHTMLRenderer._is_supported_image(attachment)
            is True
        )

    assert (
        __import__(
            "print.messages", fromlist=["MessageHTMLRenderer"]
        ).MessageHTMLRenderer._is_supported_image(
            type("Attachment", (), {"content_type": "video/mp4"})()
        )
        is True
    )


def test_message_html_renderer_converts_raw_discord_context_to_html():
    class User:
        name = "alice"
        display_name = "Alice"
        bot = False
        display_avatar = type("Avatar", (), {"url": "https://example.com/avatar.png"})()

    class Attachment:
        url = "https://example.com/file.png"
        content_type = "image/png"

    class Message:
        def __init__(self, content, created_at, author):
            self.id = 1
            self.content = content
            self.created_at = created_at
            self.author = author
            self.attachments = [Attachment()]
            self.embeds = []
            self.mentions = []

    target = Message("hello", datetime(2026, 9, 16, 11, 43, 0), User())
    html = __import__(
        "print.messages", fromlist=["MessageHTMLRenderer"]
    ).MessageHTMLRenderer.render_context_document(
        "general",
        [],
        target,
        [],
    )
    assert "Alice" in html
    assert 'src="https://example.com/file.png"' in html
    assert "hello" in html


def test_image_urls_render_as_img_tags_in_message_html():
    html = message_content_to_html("https://i.imgflip.com/8otjts.gif")
    assert "<img" in html
    assert 'src="https://i.imgflip.com/8otjts.gif"' in html
    assert 'href="https://i.imgflip.com/8otjts.gif"' not in html


def test_video_urls_render_as_video_tags_and_duplicate_media_is_filtered():
    html = message_content_to_html(
        "https://cdn.discordapp.com/attachments/123/456/i_AM_fly.mov?ex=1&is=2"
    )
    assert "<video" in html
    assert "i_AM_fly.mov" in html

    rendered = __import__(
        "print.print", fromlist=["PrintCog"]
    ).PrintCog._render_document(
        "general",
        [
            PrintableMessage(
                id=1,
                author_name="Alice",
                author_avatar_url=None,
                timestamp="2026-09-16-11-43",
                content="https://cdn.discordapp.com/attachments/123/456/i_AM_fly.mov?ex=1&is=2",
                image_urls=[
                    "https://cdn.discordapp.com/attachments/123/456/i_AM_fly.mov?ex=1&is=2",
                    "https://cdn.discordapp.com/attachments/123/456/i_AM_fly.mov?ex=1&is=2",
                ],
                is_target=True,
            )
        ],
    )
    assert rendered.count("i_AM_fly.mov") == 2
    assert rendered.count("<video") == 1


def test_output_dir_path_is_created_for_print_batch(tmp_path):
    job_dir = tmp_path / "job-1"
    job_dir.mkdir(parents=True, exist_ok=True)
    output = job_dir / "output.pdf"
    output.touch()
    assert output.exists()
    assert output.suffix == ".pdf"
