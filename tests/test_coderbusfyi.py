from coderbusfyi.coderbusfyi import CoderBusFYI


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
    assert "@alice" in notice


def test_pending_request_notice_mentions_removal_requests():
    request = {
        "title": "https://example.com/tool",
        "url": "https://example.com/tool",
        "description": "",
        "type": "remove",
        "section": "Toolbox",
        "requested_by": "@alice",
    }

    notice = CoderBusFYI.build_pending_request_notice(request)

    assert "Pending removal request" in notice
    assert "https://example.com/tool" in notice
    assert "@alice" in notice


def test_request_commands_are_guild_only_but_admin_commands_stay_global():
    assert CoderBusFYI.addrequest.guild_only is True
    assert CoderBusFYI.removerequest.guild_only is True
    assert CoderBusFYI.approverequest.guild_only is False
    assert CoderBusFYI.direct_add.guild_only is False


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

        async def send(self, message):
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
        members = [DummyMember()]

    bot = DummyBot()
    cog = CoderBusFYI.__new__(CoderBusFYI)
    cog.bot = bot

    async def runner():
        await cog._notify_admins_pending_request(
            DummyGuild(),
            {"title": "Example", "type": "add", "url": "https://example.com"},
        )
        assert bot.sent
        assert any("Pending add request" in msg for msg in bot.sent)

    import asyncio

    asyncio.run(runner())
