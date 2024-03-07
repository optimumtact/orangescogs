# Standard Imports
import logging
from typing import List, cast
import yaml
import io
from thefuzz import process

# Redbot Imports
from redbot.core import commands, checks, Config
import discord
from discord.errors import Forbidden

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_codebases")

BaseCog = getattr(commands, "Cog", object)


class CodeBases(BaseCog):
    """
    codebases module
    """

    def __init__(self, bot):
        self.bot = bot
        self.codebases_by_role = {}
        self.config: Config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.visible_config = [
            "logging_channel",
            "applier_role",
            "blesser_role",
            "bless_role",
        ]

        default_guild = {
            "applier_role": None,
            "logging_channel": False,
            "allowed_roles": [],
            "bless_role": None,
            "blesser_role": None,
        }

        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    async def codebase(self, ctx):
        """
        station
        """
        pass

    @commands.guild_only()
    @codebase.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self, ctx):
        """
        Configure the codebase module
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
        Set the channel that the codebases are logged to
        """
        try:

            await self.config.guild(ctx.guild).logging_channel.set(channel.id)
            await ctx.send(f"Channel set to {channel}")
        except (ValueError, KeyError, AttributeError) as e:
            await ctx.send(
                "There was a problem setting the channel to log to"
            )
            raise e

    async def get_log_channel(self, guild: discord.Guild):
        """
        Get the configured channel for this guild, or None if none is set or the channel doesn't exist
        """
        channel_id = await self.config.guild(guild).logging_channel()
        return cast(discord.TextChannel, guild.get_channel(channel_id))

    @config.command()
    async def set_applier_role(self, ctx, role: discord.Role):
        """
        Sets the role that can apply station roles
        """
        try:
            await self.config.guild(ctx.guild).applier_role.set(role.id)
            await ctx.send("Role set")
        except (ValueError, KeyError, AttributeError) as e:
            await ctx.send(
                "There was a problem setting the applier role"
            )
            raise e

    @config.command()
    async def set_bless_role(self, ctx, role: discord.Role):
        """
        Sets the role given on blessing
        """
        try:
            await self.config.guild(ctx.guild).bless_role.set(role.id)
            await ctx.send("Role set")
        except (ValueError, KeyError, AttributeError) as e:
            await ctx.send(
                "There was a problem setting the bless role"
            )
            raise e

    @config.command()
    async def set_blesser_role(self, ctx, role: discord.Role):
        """
        Sets the role that can bless users
        """
        try:
            await self.config.guild(ctx.guild).blesser_role.set(role.id)
            await ctx.send("Role set")
        except (ValueError, KeyError, AttributeError) as e:
            await ctx.send(
                "There was a problem setting the blesser role"
            )
            raise e

    @config.command()
    async def set_codebase_roles(self, ctx):
        """
        Set the list of roles allowed to be applied as codebase roles
        """
        if not ctx.message.attachments:
            await ctx.send("You must upload a file.")
            return

        try:
            roles = await self.get_roles_from_yaml(ctx.message.attachments[0], ctx.guild)
        except yaml.MarkedYAMLError as e:
            await ctx.send("Invalid syntax: " + str(e))
        else:
            await self.config.guild(ctx.guild).allowed_roles.set(roles)
            await ctx.send("Roles set.")

    @config.command()
    async def remove_codebase_role(self, ctx, role: discord.Role):
        """
        Remove a role from the list of codebase assignable roles
        """
        roles = await self.config.guild(ctx.guild).allowed_roles()
        if role.id in roles:
            roles.remove(role.id)
            await self.config.guild(ctx.guild).allowed_roles.set(roles)
            await ctx.send("Role removed")
            return
        await ctx.send("invalid role or role not in list of roles")

    @config.command()
    async def add_codebase_role(self, ctx, role: discord.Role):
        """
        Add a role to the list of codebase assignable roles
        """
        roles = await self.config.guild(ctx.guild).allowed_roles()
        if role.id not in roles:
            roles.append(role.id)
            await self.config.guild(ctx.guild).allowed_roles.set(roles)
            await ctx.send("Role added")
            return
        await ctx.send("invalid role or already in list")

    @config.command()
    async def get_server_roles(self, ctx):
        """
        Get all server role as a yaml, helps when setting up codebase roles in bulk
        """
        file = await self.get_server_roles_as_yaml(ctx.guild)
        await ctx.send("here are the guild roles", file=file)

    @config.command()
    async def get_codebase_roles(self, ctx):
        """
        Get all server role as a yaml, helps when setting up codebase roles in bulk
        """
        file = await self.get_codebase_roles_as_yaml(ctx)
        await ctx.send("here are the current codebase roles", file=file)

    @codebase.command(aliases=["del", "unapply"])
    async def remove(self, ctx, user: discord.Member, *, codebase: str):
        """
        remove a codebase role as long as you are permissioned and a member of that codebase
        """

        if isinstance(codebase, str):
            codebase = await self.name_to_role(ctx.guild, codebase)
        if not codebase:
            await ctx.send("I couldn't find that role by name")
            return
        if not await self.validate_user_and_codebase(ctx, ctx.author, codebase):
            return
        reason = f'codebase {codebase} removed from {user} by {ctx.author}'
        try:
            await user.remove_roles(
                codebase,
                reason=reason,
            )
            await self.send_log_message(ctx.guild, reason, ctx.author, user, ctx.message.jump_url)
            await ctx.send("codebase has been removed")
        except (Forbidden):
            await ctx.send("I do not have permission to change the roles")

    @commands.guild_only()
    @commands.command()
    async def curse(self, ctx, user: discord.Member):
        blesser_role = await self.config.guild(ctx.guild).blesser_role()
        blesser_role = ctx.guild.get_role(blesser_role)
        bless_role = await self.config.guild(ctx.guild).bless_role()
        bless_role = ctx.guild.get_role(bless_role)

        if blesser_role not in ctx.author.roles:
            await ctx.send("You are not authorised to do that")
            return False

        reason = f'{ctx.author} blessed {user}'
        await user.add_roles(
            bless_role,
            reason=reason,
        )
        await ctx.send(f"{user} is cursed with a vague sense of foreboding")

    @commands.guild_only()
    @commands.command()
    async def bless(self, ctx, user: discord.Member):
        blesser_role = await self.config.guild(ctx.guild).blesser_role()
        blesser_role = ctx.guild.get_role(blesser_role)
        bless_role = await self.config.guild(ctx.guild).bless_role()
        bless_role = ctx.guild.get_role(bless_role)

        if blesser_role not in ctx.author.roles:
            await ctx.send("You are not authorised to do that")
            return False

        reason = f'{ctx.author} blessed {user}'
        await user.add_roles(
            bless_role,
            reason=reason,
        )
        await ctx.send(f"{user} blessed")

    @codebase.command(aliases=["apply"])
    async def add(self, ctx, user: discord.Member, *, codebase: str):
        """
        Set a role on the user, as long as you have the appropriate granting role
        and the same codebase role
        """

        if isinstance(codebase, str):
            codebase = await self.name_to_role(ctx.guild, codebase)
        if not codebase:
            await ctx.send("I couldn't find that role by name")
            return
        if not await self.validate_user_and_codebase(ctx, ctx.author, codebase):
            return

        reason = f'Requested codebase {codebase} by {ctx.author} for {user}'
        try:
            await user.add_roles(
                codebase,
                reason=reason,
            )
            await self.send_log_message(ctx.guild, reason, ctx.author, user, ctx.message.jump_url)
            await ctx.send("codebase has been added")
        except (Forbidden):
            await ctx.send("I do not have permission to change the roles")

    async def send_log_message(self, guild: discord.Guild, message: str, source: discord.Member, target: discord.Member, jump_url: str):
        """
        Send a log message about a codebase action happening
        """
        channel: discord.TextChannel = await self.get_log_channel(guild)
        if channel:
            embed = discord.Embed(url=jump_url, title="__codebase action:__")
            embed.add_field(name="Source", value=f"{source} <@{source.id}>", inline=False)
            embed.add_field(name="Target", value=f"{target} <@{target.id}>", inline=False)
            embed.add_field(name="Action", value=message, inline=False)
            log.info(type(channel))
            await channel.send(embed=embed)

    async def validate_user_and_codebase(self, ctx, applier: discord.Member, codebase: discord.Role):
        """
        Validate that a given applier can award the given discord role, sends messages to the given context for feedback
        """

        if isinstance(codebase, str):
            codebase = await self.name_to_role(ctx.guild, codebase)
        if not codebase:
            await ctx.send("I couldn't find that role by name")
            return
        applier_role = await self.config.guild(ctx.guild).applier_role()
        applier_role = ctx.guild.get_role(applier_role)
        allowed_roles = await self.config.guild(ctx.guild).allowed_roles()
        if codebase.id not in allowed_roles:
            await ctx.send("Not a valid codebase role")
            return False

        if applier_role not in ctx.author.roles:
            await ctx.send("You are not authorised to do that")
            return False

        blesser_role = await self.config.guild(ctx.guild).blesser_role()
        blesser_role = ctx.guild.get_role(blesser_role)

        if codebase not in ctx.author.roles and blesser_role not in ctx.author.roles:
            await ctx.send(f"You cannot apply a codebase role for a codebase you are not a member of: {codebase.name}")
            return False

        return True

    async def get_roles_from_yaml(self, source: discord.Attachment, guild: discord.Guild) -> List:
        """get roles from a YAML file."""
        final = []
        with io.BytesIO() as fp:
            await source.save(fp)
            rules = yaml.safe_load(fp)
            for id, name in rules.items():
                if not guild.get_role(id):
                    continue
                final.append(id)
        return final

    async def get_codebase_roles_as_yaml(self, ctx) -> discord.File:
        """Return the list of current valid codebase roles as id => name yaml"""
        final_roles = {}
        codebase_roles = await self.config.guild(ctx.guild).allowed_roles()
        for c_role in codebase_roles:
            role = ctx.guild.get_role(c_role)
            if not role:
                continue
            final_roles[role.id] = role.name
        fp = io.BytesIO(yaml.dump(final_roles, default_flow_style=False).encode("utf-8"))
        return discord.File(fp, filename="codebaseroles.yaml")

    async def get_server_roles_as_yaml(self, guild: discord.Guild) -> discord.File:
        """Get a YAML file for all roles in a guild"""
        guild_roles = {}
        roles = await guild.fetch_roles()
        for role in roles:
            guild_roles[role.id] = role.name
        fp = io.BytesIO(yaml.dump(guild_roles, default_flow_style=False).encode("utf-8"))
        return discord.File(fp, filename="roles.yaml")

    async def name_to_role(self, guild: discord.Guild, name) -> discord.Role:
        names = []
        name2role = {}
        for role in await guild.fetch_roles():
            names.append(role.name)
            name2role[role.name] = role
        match, score = process.extractOne(name, names)
        log.error(f"{match}, {score}")
        if score < 70:
            return None
        return name2role[match]
