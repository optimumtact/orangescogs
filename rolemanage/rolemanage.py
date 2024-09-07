# Standard Imports
import json
import logging
import re
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Any, Dict, cast

import discord
from discord.errors import Forbidden

# Redbot Imports
from redbot.core import Config, checks, commands

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_rolemanage")

BaseCog = getattr(commands, "Cog", object)


class RoleManage(BaseCog):
    """
    Role manager module
    """

    def __init__(self, bot):
        self.bot = bot
        self.rolemanages_by_role = {}
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.visible_config = [
            "enabled",
            "role_map",
            "logging_channel",
            "rolemanages",
        ]

        default_guild = {
            "enabled": True,
            "role_map": {},
            "logging_channel": False,
        }

        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    async def rolemanage(self, ctx):
        """
        rolemanage module
        """
        pass

    @commands.guild_only()
    @rolemanage.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self, ctx):
        """
        Configure the rolemanage module
        """
        pass

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.guild(ctx.guild).all()
        embed: discord.Embed = discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:", value=v, inline=False)
            else:
                embed.add_field(name=f"{k}:", value="`redacted`", inline=False)
        await ctx.send(embed=embed)

    @config.command()
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        """
        Set the channel that the rolemanages are logged to
        """
        try:

            await self.config.guild(ctx.guild).logging_channel.set(channel.id)
            await ctx.send(f"Channel set to {channel}")
        except (ValueError, KeyError, AttributeError) as e:
            await ctx.send("There was a problem setting the channel to log to")
            raise e

    async def send_log_message(
        self,
        guild: discord.Guild,
        message: str,
        source: discord.Member,
        target: discord.Member,
        jump_url: str,
    ):
        """
        Send a log message about a rolemanage action happening
        """
        channel: discord.TextChannel = await self.get_log_channel(guild)
        if channel:
            embed = discord.Embed(url=jump_url, title="__rolemanage action:__")
            embed.add_field(name="Source", value=source, inline=False)
            embed.add_field(name="Target", value=target, inline=False)
            embed.add_field(name="Action", value=message, inline=False)
            await channel.send(embed=embed)

    async def get_log_channel(self, guild: discord.Guild):
        """
        Get the configured channel for this guild, or None if none is set or the channel doesn't exist
        """
        channel_id = await self.config.guild(guild).logging_channel()
        return cast(discord.TextChannel, guild.get_channel(channel_id))

    @config.command()
    async def roleadd(self, ctx, sourcerole: discord.Role, targetrole: discord.Role):
        """
        Sets that a given role can manage a given role by applying and removing it
        """
        roles = await self.config.guild(ctx.guild).role_map()
        if sourcerole.id in roles:
            if targetrole.id not in roles[sourcerole.id]:
                roles[sourcerole.id].append(targetrole.id)
        else:
            roles[sourcerole.id] = list()
            roles[sourcerole.id].append(targetrole.id)
        await self.config.guild(ctx.guild).role_map.set(roles)
        await ctx.send(f"Role {sourcerole} can now manage {targetrole}")

    @config.command()
    async def roledel(self, ctx, sourcerole: discord.Role, targetrole: discord.Role):
        """
        Removes that a given role can manage a given role by applying and removing it
        """
        roles = await self.config.guild(ctx.guild).role_map()
        if sourcerole.id in roles:
            roles[sourcerole.id].remove(targetrole.id)
        await self.config.guild(ctx.guild).role_map.set(roles)
        await ctx.send(f"Role {sourcerole} can no longer manage {targetrole}")

    @config.command()
    async def enable(self, ctx):
        """
        Enable the plugin
        """
        try:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("The module is now enabled")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem enabling the module")

    @rolemanage.command()
    async def remove(self, ctx, user: discord.Member, role: discord.Role):
        """
        remove any rolemanage on the targeted user
        """
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            await ctx.send("This module is not enabled")
            return

        role_map_dict = await self.config.guild(ctx.guild).role_map()
        allowed_roles = set()
        for author_role in ctx.author.roles:
            roleid = str(author_role.id)
            if roleid in role_map_dict:
                allowed_roles.update(role_map_dict[roleid])
                log.debug(f"found role mappings {role_map_dict[roleid]}")

        if role.id not in allowed_roles:
            log.debug(f"The {role} was not in the {allowed_roles}")
            await ctx.send("You are not authorised to remove this role")
            return
        reason = f"Role {role} requested to be removed by {ctx.author}"
        try:
            await user.remove_roles(role, reason=reason)
        except Forbidden:
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("I do not have permission to manage roles in this server")

        await self.send_log_message(
            ctx.guild,
            reason,
            ctx.author,
            user,
            ctx.message.jump_url,
        )
        await ctx.send(f"{role.name} has been removed")

    @rolemanage.command()
    async def apply(self, ctx, user: discord.Member, role: discord.Role):
        """
        remove any rolemanage on the targeted user
        """
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            await ctx.send("This module is not enabled")
            return

        role_map_dict = await self.config.guild(ctx.guild).role_map()
        allowed_roles = set()
        for author_role in ctx.author.roles:
            roleid = str(author_role.id)
            if roleid in role_map_dict:
                allowed_roles.update(role_map_dict[roleid])

        if role.id not in allowed_roles:
            log.debug(f"The {role} was not in the {allowed_roles}")
            await ctx.send("You are not authorised to add this role")
            return

        reason = f"Role {role} requested to be added by {ctx.author}"
        try:
            await user.add_roles(role, reason=reason)
        except Forbidden:
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("I do not have permission to manage roles in this server")

        await self.send_log_message(
            ctx.guild,
            reason,
            ctx.author,
            user,
            ctx.message.jump_url,
        )
        await ctx.send(f"{role.name} has been added")
