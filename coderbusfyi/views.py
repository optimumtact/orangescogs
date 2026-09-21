from __future__ import annotations

import discord


class PendingRequestActionButton(discord.ui.Button):
    def __init__(self, cog, action, request, label, style):
        self.cog = cog
        self.action = action
        self.request = request
        super().__init__(
            label=label,
            style=style,
            custom_id=cog.build_pending_request_action_custom_id(request, action),
        )

    async def callback(self, interaction: discord.Interaction):
        await self.cog._handle_pending_request_action(
            interaction, self.action, self.request
        )


class PendingRequestActionView(discord.ui.View):
    def __init__(self, cog, request):
        super().__init__(timeout=None)
        self.cog = cog
        self.request = request
        self.add_item(
            PendingRequestActionButton(
                cog=cog,
                action="approve",
                request=request,
                label="Approve",
                style=discord.ButtonStyle.green,
            )
        )
        self.add_item(
            PendingRequestActionButton(
                cog=cog,
                action="deny",
                request=request,
                label="Deny",
                style=discord.ButtonStyle.red,
            )
        )


class PendingRequestViewManager:
    def __init__(self, bot, cog):
        self.bot = bot
        self.cog = cog

    def build_pending_request_action_view(self, request):
        return PendingRequestActionView(self.cog, request)

    def register_pending_request_view(self, request):
        view = self.build_pending_request_action_view(request)
        message_id = request.get("message_id")
        if message_id is not None:
            try:
                message_id = int(message_id)
            except (TypeError, ValueError):
                message_id = None
        if message_id is None:
            self.bot.add_view(view)
        else:
            self.bot.add_view(view, message_id=message_id)
        return view

    async def rehydrate_pending_request_views(self, pending_requests):
        for request in pending_requests:
            self.register_pending_request_view(request)
