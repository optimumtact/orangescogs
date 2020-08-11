#Standard Imports
import logging
from typing import Union

#Discord Imports
from discord import TextChannel, Embed

#Redbot Imports
from redbot.core import commands, checks, Config

__version__ = "1.0.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_based")

BaseCog = getattr(commands, "Cog", object)

class Based(BaseCog):
    """
    Connector that will integrate with any database using the latest tg schema, provides utility functionality
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=672261474290237490, force_registration=True)
        self.visible_config = ["active_channels"]

        default_config = {
            "active_channels": []
        }

        self.config.register_global(**default_config)
    
        self.channel_map = None

    async def load_config(self):
        if not self.channel_map:
            self.channel_map = await self.config.active_channels()

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.load_config()

        if message.author == self.bot.user:
            return
        if str(message.channel.id) in self.channel_map and message.content.lower().startswith('based'):
                await message.channel.send('Based on what?')


    @commands.guild_only()
    @commands.group()
    async def based(self,ctx):
        """
        The based cog
        """
        pass


    @based.group()
    @checks.admin_or_permissions(administrator=True)
    async def config(self,ctx):
        """
        Configure based cog permissions
        """
        pass

    @config.command()
    async def add_channel(self, ctx, channel: str):
        """
        Add a channel we respond in
        """
        await self.load_config()
        try:
            if channel not in self.channel_map:
                self.channel_map.append(channel)
            await self.config.active_channels.set(self.channel_map)
            await ctx.send(f"Channel added")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem adding the channel")

    @config.command()
    async def remove_channel(self, ctx, channel: str):
        """
        Add a channel we respond in
        """
        await self.load_config()
        try:
            self.channel_map.remove(channel)
            await self.config.active_channels.set(self.channel_map)
            await ctx.send(f"Channel removed")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem adding the channel")

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.all()
        embed=Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:",value=v,inline=False)
            else:
                embed.add_field(name=f"{k}:",value="`redacted`",inline=False)
        await ctx.send(embed=embed)
