from coderbusfyi.coderbusfyi import CoderBusFYI
from coderbusfyi.views import PendingRequestActionView, PendingRequestViewManager


def test_parse_ini_entries_handles_sections_and_values():
    source = """
[Core references]
DM Reference = https://ref.dm-lang.org/ | Unofficial DM
reference that is easy to use.

[Toolbox]
Map Diff Bot = https://github.com/apps/mapdiffbot-2 | Github App that shows map changes

"""

    entries = CoderBusFYI.parse_ini_entries(source)

    assert entries[0]["section"] == "Core references"
    assert entries[0]["title"] == "DM Reference"
    assert entries[0]["url"] == "https://ref.dm-lang.org/"
    assert entries[0]["description"] == "Unofficial DM reference that is easy to use."

    assert entries[1]["section"] == "Toolbox"
    assert entries[1]["title"] == "Map Diff Bot"
    assert entries[1]["url"] == "https://github.com/apps/mapdiffbot-2"
    assert entries[1]["description"] == "Github App that shows map changes"


def test_build_ini_from_entries_round_trips_sections():
    entries = [
        {
            "section": "Toolbox",
            "title": "Example Tool",
            "url": "https://example.com",
            "description": "Helpful",
        },
        {
            "section": "Learning paths",
            "title": "Example Course",
            "url": "https://example.com/course",
            "description": "Course",
        },
    ]

    text = CoderBusFYI.entries_to_ini(entries)

    assert "[Toolbox]" in text
    assert "Example Tool = https://example.com | Helpful" in text
    assert "[Learning paths]" in text
    assert "Example Course = https://example.com/course | Course" in text


def test_find_pending_request_by_url_ignores_title():
    pending = [
        {
            "title": "Example Tool",
            "url": "https://example.com/tool",
            "description": "Helpful",
            "type": "add",
            "section": "Toolbox",
        },
        {
            "title": "https://example.com/remove-me",
            "url": "https://example.com/remove-me",
            "description": "",
            "type": "remove",
            "section": "Toolbox",
        },
    ]

    found = CoderBusFYI.find_pending_request_by_url(pending, "https://example.com/tool")
    assert found is not None
    assert found["type"] == "add"
    assert found["title"] == "Example Tool"

    found_remove = CoderBusFYI.find_pending_request_by_url(
        pending, "https://example.com/remove-me"
    )
    assert found_remove is not None
    assert found_remove["type"] == "remove"


def test_collect_sections_from_ini_data():
    source = """
[Core references]
DM Reference = https://ref.dm-lang.org/ | Unofficial DM

[Toolbox]
Map Diff Bot = https://github.com/apps/mapdiffbot-2 | Github App

[Learning paths]
Another = https://example.com | Example
"""

    sections = CoderBusFYI.collect_sections(source)

    assert sections == ["Core references", "Toolbox", "Learning paths"]


def test_pending_request_notice_mentions_request_type_and_section():
    request = {
        "title": "Example Tool",
        "url": "https://example.com/tool",
        "description": "Helpful",
        "type": "add",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_pending_request_notice(request)

    assert "Pending add request" in notice
    assert "Example Tool" in notice
    assert "Toolbox" in notice
    assert "<https://example.com/tool>" in notice
    assert "Description: Helpful" in notice
    assert "@alice" in notice


def test_pending_request_notice_mentions_removal_requests():
    request = {
        "title": "https://example.com/tool",
        "url": "https://example.com/tool",
        "description": "Outdated and broken",
        "type": "remove",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_pending_request_notice(request)

    assert "Pending removal request" in notice
    assert "<https://example.com/tool>" in notice
    assert "Reason: Outdated and broken" in notice
    assert "@alice" in notice


def test_requester_resolution_notice_mentions_actor_and_status():
    request = {
        "title": "Example Tool",
        "url": "https://example.com/tool",
        "description": "Helpful",
        "type": "add",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_requester_resolution_notice(
        request,
        "approve",
        type("Actor", (), {"mention": "<@123>"})(),
    )

    assert "approved by <@123>" in notice.lower()
    assert "example tool" in notice.lower()


def test_pending_request_action_custom_id_includes_user_and_url():
    request = {"requested_by_id": 12345, "url": "https://example.com/tool"}
    custom_id = CoderBusFYI.build_pending_request_action_custom_id(request, "approve")

    assert custom_id.startswith("approve:12345:")
    action, requester_id, url = CoderBusFYI.parse_pending_request_action_custom_id(
        custom_id
    )
    assert action == "approve"
    assert requester_id == "12345"
    assert url == "https://example.com/tool"


def test_pending_request_resolution_notice_mentions_actor():
    request = {
        "title": "Example Tool",
        "url": "https://example.com/tool",
        "description": "Helpful",
        "type": "add",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_pending_request_resolution_notice(
        request,
        "approve",
        type("Actor", (), {"mention": "<@123>"})(),
    )

    assert "Pending add request" in notice
    assert "accepted by <@123>" in notice.lower()


def test_pending_request_resolution_notice_uses_bee_for_denied_actions():
    request = {
        "title": "Example Tool",
        "url": "https://example.com/tool",
        "description": "Helpful",
        "type": "add",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_pending_request_resolution_notice(
        request,
        "deny",
        type("Actor", (), {"mention": "<@123>"})(),
    )

    assert "🐝 request denied by <@123>" in notice.lower()


def test_get_notification_channel_uses_guild_object_not_id():
    class DummyConfig:
        def __init__(self):
            self.guild_calls = []

        def guild(self, guild):
            self.guild_calls.append(guild)
            return type(
                "GuildGroup",
                (),
                {
                    "notification_channel_id": lambda self: __import__("asyncio").sleep(
                        0, result=987
                    )
                },
            )()

    class DummyGuild:
        id = 123

        def get_channel(self, channel_id):
            assert channel_id == 987
            return "channel"

    cog = CoderBusFYI.__new__(CoderBusFYI)
    cog.config = DummyConfig()
    cog.bot = type("Bot", (), {"get_guild": lambda self, guild_id: None})()

    result = __import__("asyncio").run(cog._get_notification_channel(DummyGuild()))
    assert result == "channel"
    assert len(cog.config.guild_calls) == 1
    assert cog.config.guild_calls[0].id == 123


def test_get_notification_channel_accepts_guild_id_and_coerces_to_object():
    class DummyConfig:
        def __init__(self):
            self.guild_calls = []

        def guild(self, guild):
            self.guild_calls.append(guild)
            return type(
                "GuildGroup",
                (),
                {
                    "notification_channel_id": lambda self: __import__("asyncio").sleep(
                        0, result=111
                    )
                },
            )()

    class DummyGuild:
        id = 456

        def get_channel(self, channel_id):
            assert channel_id == 111
            return "channel-from-id"

    dummy_guild = DummyGuild()
    cog = CoderBusFYI.__new__(CoderBusFYI)
    cog.config = DummyConfig()
    cog.bot = type(
        "Bot",
        (),
        {"get_guild": lambda self, guild_id: dummy_guild if guild_id == 456 else None},
    )()

    result = __import__("asyncio").run(cog._get_notification_channel(456))
    assert result == "channel-from-id"
    assert len(cog.config.guild_calls) == 1
    assert cog.config.guild_calls[0].id == 456


def test_request_commands_are_guild_only_but_admin_commands_stay_global():
    assert CoderBusFYI.addrequest.guild_only is True
    assert CoderBusFYI.removerequest.guild_only is True
    assert CoderBusFYI.approverequest.guild_only is False
    assert CoderBusFYI.direct_add.guild_only is False


def test_removerequest_requires_reason_parameter():
    param_names = [param.name for param in CoderBusFYI.removerequest.parameters]
    assert "reason" in param_names


def test_admin_section_commands_match_ui_intent():
    assert hasattr(CoderBusFYI, "addsection_autocomplete") is False
    assert hasattr(CoderBusFYI, "removesection_autocomplete") is True


def test_resource_choice_names_include_titles_and_urls():
    source = """
[Toolbox]
Example Tool = https://example.com/tool | Helpful
Another Tool = https://example.com/other | More info
"""

    choices = CoderBusFYI.build_resource_choices(source)

    assert choices[0].name == "Example Tool - https://example.com/tool"
    assert choices[0].value == "https://example.com/tool"
    assert choices[1].name == "Another Tool - https://example.com/other"


def test_pending_request_choices_include_title_and_url():
    pending = [
        {
            "title": "Queued Tool",
            "url": "https://example.com/queued",
            "description": "Queued",
            "type": "add",
            "section": "Toolbox",
        },
        {
            "title": "Queued Remove",
            "url": "https://example.com/remove-me",
            "description": "",
            "type": "remove",
            "section": "Toolbox",
        },
    ]

    choices = CoderBusFYI.build_pending_request_choices(pending)

    assert choices[0].name == "Queued Tool - https://example.com/queued"
    assert choices[0].value == "https://example.com/queued"
    assert choices[1].name == "Queued Remove - https://example.com/remove-me"


def test_notify_admins_uses_owner_ids_not_get_owner():
    class DummyUser:
        def __init__(self, user_id, sent):
            self.id = user_id
            self.sent = sent

        async def send(self, message, *args, **kwargs):
            self.sent.append(message)

    class DummyBot:
        owner_id = 42
        owner_ids = {42, 99}

        def __init__(self):
            self.sent = []
            self.users = {42: DummyUser(42, self.sent), 99: DummyUser(99, self.sent)}

        def get_user(self, user_id):
            return self.users.get(user_id)

        async def fetch_user(self, user_id):
            if user_id in self.users:
                return self.users[user_id]
            raise RuntimeError("unexpected")

    class DummyMember:
        bot = False
        id = 5
        guild_permissions = type(
            "Perms", (), {"administrator": False, "manage_guild": False}
        )()

    class DummyGuild:
        id = 123
        members = [DummyMember()]

    bot = DummyBot()
    cog = CoderBusFYI.__new__(CoderBusFYI)
    cog.bot = bot
    cog.view_manager = PendingRequestViewManager(bot, cog)

    async def runner():
        await cog._notify_admins_pending_request(
            DummyGuild(),
            {"title": "Example", "type": "add", "url": "https://example.com"},
        )
        assert bot.sent
        assert any("Pending add request" in msg for msg in bot.sent)

    import asyncio

    asyncio.run(runner())


def test_pending_request_action_view_is_persistent():
    cog = CoderBusFYI.__new__(CoderBusFYI)
    view = PendingRequestActionView(
        cog,
        {
            "title": "Example Tool",
            "url": "https://example.com/tool",
            "requested_by_id": 123,
        },
    )

    assert view.timeout is None
    assert len(view.children) == 2


def test_pending_request_view_manager_rehydrates_views_with_message_ids():
    class DummyBot:
        def __init__(self):
            self.calls = []

        def add_view(self, view, message_id=None):
            self.calls.append((view, message_id))

    cog = CoderBusFYI.__new__(CoderBusFYI)
    bot = DummyBot()
    manager = PendingRequestViewManager(bot, cog)

    import asyncio

    asyncio.run(
        manager.rehydrate_pending_request_views(
            [
                {
                    "title": "Example Tool",
                    "url": "https://example.com/tool",
                    "requested_by_id": 123,
                    "message_id": 987654321,
                }
            ]
        )
    )

    assert len(bot.calls) == 1
    view, message_id = bot.calls[0]
    assert isinstance(view, PendingRequestActionView)
    assert view.timeout is None
    assert message_id == 987654321


def test_pending_request_logging_helpers_emit_request_details(caplog):
    cog = CoderBusFYI.__new__(CoderBusFYI)

    with caplog.at_level("INFO", logger="red.oranges_coderbusfyi"):
        cog._log_pending_request_created(
            {
                "type": "add",
                "requested_by": "@alice",
                "requested_by_id": 123,
                "title": "Example Tool",
                "url": "https://example.com/tool",
                "description": "Helpful",
                "section": "Toolbox",
            }
        )
        cog._log_pending_request_created(
            {
                "type": "remove",
                "requested_by": "@alice",
                "requested_by_id": 123,
                "title": "https://example.com/tool",
                "url": "https://example.com/tool",
                "description": "Outdated and broken",
                "section": "Toolbox",
            }
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "Pending add request created by @alice (user_id=123)" in message
        and "title=Example Tool" in message
        and "url=https://example.com/tool" in message
        and "description=Helpful" in message
        for message in messages
    )
    assert any(
        "Pending remove request created by @alice (user_id=123)" in message
        and "url=https://example.com/tool" in message
        and "reason=Outdated and broken" in message
        for message in messages
    )


def test_pending_request_resolution_logging_helpers_emit_actor_and_source(caplog):
    cog = CoderBusFYI.__new__(CoderBusFYI)

    with caplog.at_level("INFO", logger="red.oranges_coderbusfyi"):
        cog._log_pending_request_resolution(
            {
                "type": "add",
                "requested_by": "@alice",
                "requested_by_id": 123,
                "title": "Example Tool",
                "url": "https://example.com/tool",
                "description": "Helpful",
                "section": "Toolbox",
            },
            "approve",
            type("Actor", (), {"mention": "<@123>"})(),
            "command",
        )
        cog._log_pending_request_resolution(
            {
                "type": "remove",
                "requested_by": "@alice",
                "requested_by_id": 123,
                "title": "https://example.com/tool",
                "url": "https://example.com/tool",
                "description": "Outdated and broken",
                "section": "Toolbox",
            },
            "deny",
            type("Actor", (), {"mention": "<@456>"})(),
            "button",
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "Pending add request approved via command by <@123>" in message
        and "title=Example Tool" in message
        and "url=https://example.com/tool" in message
        for message in messages
    )
    assert any(
        "Pending remove request denied via button by <@456>" in message
        and "url=https://example.com/tool" in message
        and "reason=Outdated and broken" in message
        for message in messages
    )


def test_direct_admin_logging_helper_records_action_details(caplog):
    cog = CoderBusFYI.__new__(CoderBusFYI)

    with caplog.at_level("INFO", logger="red.oranges_coderbusfyi"):
        cog._log_direct_admin_action(
            "add item",
            type("Actor", (), {"mention": "<@789>"})(),
            title="Example Tool",
            url="https://example.com/tool",
            description="Helpful",
            section="Toolbox",
        )
        cog._log_direct_admin_action(
            "remove section",
            type("Actor", (), {"mention": "<@789>"})(),
            section="Toolbox",
        )

    messages = [record.getMessage() for record in caplog.records]
    assert any(
        "Admin add item by <@789>" in message
        and "title=Example Tool" in message
        and "url=https://example.com/tool" in message
        and "description=Helpful" in message
        and "section=Toolbox" in message
        for message in messages
    )
    assert any(
        "Admin remove section by <@789>" in message
        and "section=Toolbox" in message
        for message in messages
    )
