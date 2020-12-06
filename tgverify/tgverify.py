#Standard Imports
import logging
from typing import Union

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

from tgcommon.errors import TGRecoverableError, TGUnrecoverableError
from tgcommon.util import normalise_to_ckey
from typing import cast

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_tgverify")

BaseCog = getattr(commands, "Cog", object)

class TGverify(BaseCog):
    """
    Connector that will integrate with any database using the latest tg schema, provides utility functionality
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=672261474290237490, force_registration=True)
        self.visible_config = ["min_living_minutes", "verified_role", "instructions_link", "welcomegreeting", "disabledgreeting", "bunkerwarning", "bunker", "welcomechannel"]

        default_guild = {
            "min_living_minutes": 60,
            "verified_role": None,
            "verified_living_role": None,
            "instructions_link": "",
            "welcomegreeting": "",
            "disabledgreeting": "",
            "bunkerwarning": "",
            "bunker": False,
            "disabled": False,
            "welcomechannel": "",
        }

        self.config.register_guild(**default_guild)



    @commands.guild_only()
    @commands.group()
    @checks.mod_or_permissions(administrator=True)
    async def tgverify(self,ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @commands.guild_only()
    @tgverify.group()
    @checks.mod_or_permissions(administrator=True)
    async def config(self,ctx):
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @config.command()
    async def current(self, ctx):
        """
        Gets the current settings for the verification system
        """
        settings = await self.config.guild(ctx.guild).all()
        embed=discord.Embed(title="__Current settings:__")
        for k, v in settings.items():
            # Hide any non whitelisted config settings (safety moment)
            if k in self.visible_config:
                if v == "":
                    v = None
                embed.add_field(name=f"{k}:",value=v,inline=False)
            else:
                embed.add_field(name=f"{k}:",value="`redacted`",inline=False)
        await ctx.send(embed=embed)


    @config.command()
    async def living_minutes(self, ctx, min_living_minutes: int = None):
        """
        Sets the minimum required living minutes before this bot will apply a verification role to a user
        """
        try:
            if min_living_minutes is None:
                await self.config.guild(ctx.guild).min_living_minutes.set(0)
                await ctx.send(f"Minimum living minutes required for verification removed!")
            else:
                await self.config.guild(ctx.guild).min_living_minutes.set(min_living_minutes)
                await ctx.send(f"Minimum living minutes required for verification set to: `{min_living_minutes}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the minimum required living minutes")

    @config.command()
    async def instructions_link(self, ctx, instruction_link: str):
        """
        Sets the link to further instructions on how to generate verification information
        """
        try:
            await self.config.guild(ctx.guild).instructions_link.set(instruction_link)
            await ctx.send(f"Instruction link set to: `{instruction_link}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the instructions link")

    @config.command()
    async def welcome_channel(self, ctx, channel: discord.TextChannel):
        """
        Sets the channel to send the welcome message
        If channel isn"t specified, the guild's default channel will be used
        """
        guild = ctx.message.guild
        guild_settings = await self.config.guild(guild).welcomechannel()
        if channel is None:
            channel = ctx.message.channel
        if not channel.permissions_for(ctx.me).send_messages:
            msg = "I do not have permissions to send messages to {channel}".format(
                channel=channel.mention
            )
            await ctx.send(msg)
            return
        guild_settings = channel.id
        await self.config.guild(guild).welcomechannel.set(guild_settings)
        msg = "I will now send welcome messages to {channel}".format(channel=channel.mention)
        await channel.send(msg)
    
    @config.command()
    async def welcome_greeting(self, ctx, welcomegreeting: str):
        """
        Sets the welcoming greeting
        """
        try:
            await self.config.guild(ctx.guild).welcomegreeting.set(welcomegreeting)
            await ctx.send(f"Welcome greeting set to: `{welcomegreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the Welcome greeting")

    @config.command()
    async def disabled_greeting(self, ctx, disabledgreeting: str):
        """
        Sets the welcoming greeting when the verification system is disabled
        """
        try:
            await self.config.guild(ctx.guild).disabledgreeting.set(disabledgreeting)
            await ctx.send(f"Disabled greeting set to: `{disabledgreeting}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the disabled greeting")

    @config.command()
    async def bunker_warning(self, ctx, bunkerwarning: str):
        """
        Sets the additional message added to the greeting message when the bunker is on
        """
        try:
            await self.config.guild(ctx.guild).bunkerwarning.set(bunkerwarning)
            await ctx.send(f"Bunker warning set to: `{bunkerwarning}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the bunker warning")
    
    @tgverify.command()
    async def bunker(self, ctx):
        """
        Toggle bunker status on or off
        """
        try:
            bunker = await self.config.guild(ctx.guild).bunker()
            bunker = not bunker
            await self.config.guild(ctx.guild).bunker.set(bunker)
            if bunker:
                await ctx.send(f"The bunker warning is now on")
            else:
                await ctx.send(f"The bunker warning is now off")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem toggling the bunker")
    
    @tgverify.command()
    async def broken(self, ctx):
        """
        For when verification breaks
        """
        try:
            disabled = await self.config.guild(ctx.guild).disabled()
            disabled = not disabled
            await self.config.guild(ctx.guild).disabled.set(disabled)
            if disabled:
                await ctx.send(f"The verification system is now off")
            else:
                await ctx.send(f"The verification system is now on")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem toggling the disabled flag")

    @config.command()
    async def verified_role(self, ctx, verified_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_role)
            if not role:
                return await ctx.send(f"This is not a valid role for this discord!")
            if verified_role is None:
                await self.config.guild(ctx.guild).verified_role.set(None)
                await ctx.send(f"No role will be set when the user verifies!")
            else:
                await self.config.guild(ctx.guild).verified_role.set(verified_role)
                await ctx.send(f"When a user meets minimum verification this role will be applied: `{verified_role}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the verified role")

    @config.command()
    async def verified_living_role(self, ctx, verified_living_role: int = None):
        """
        Set what role is applied when a user verifies
        """
        try:
            role = ctx.guild.get_role(verified_living_role)
            if not role:
                return await ctx.send(f"This is not a valid role for this discord!")
            if verified_living_role is None:
                await self.config.guild(ctx.guild).verified_living_role.set(None)
                await ctx.send(f"No role will be set when the user verifies!")
            else:
                await self.config.guild(ctx.guild).verified_living_role.set(verified_living_role)
                await ctx.send(f"When a user meets minimum verification this role will be applied: `{verified_living_role}`")

        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the verified role")

    @tgverify.command()
    async def discords(self, ctx, ckey: str):
        """
        List all past discord accounts this ckey has verified with
        """
        tgdb = self.get_tgdb()
        ckey = normalise_to_ckey(ckey)
        message = await ctx.send("Collecting discord accounts for ckey....")
        async with ctx.typing():
            embed=discord.Embed(color=await ctx.embed_color())
            embed.set_author(name=f"Discord accounts historically linked to {str(ckey).title()}")
            links = await tgdb.all_discord_links_for_ckey(ctx, ckey)
            if len(links) <= 0:
                return await message.edit(content="No discord accounts found for this ckey")

            names = ""
            for link in links:
                names += f"User linked <@{link.discord_id}> on {link.timestamp}, current account: {link.validity}\n"

            embed.add_field(name="__Discord accounts__", value=names, inline=False)
            await message.edit(content=None, embed=embed)


    @tgverify.command()
    async def whois(self, ctx, discord_user: discord.User):
        """
        Return the ckey attached to the given discord user, if they have one
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Finding out the ckey of user....")
        async with ctx.typing():
            # Attempt to find the discord ids based on the one time token passed in.
            discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
            if discord_link:
                message = await message.edit(content=f"This discord user is linked to the ckey {discord_link.ckey}")
            else:
                message = await message.edit(content=f"This discord user has no ckey linked")

    @tgverify.command()
    async def deverify(self, ctx, discord_user: discord.User):
        """
        Deverifies the ckey linked to this user, all historical verifications will be removed, the user will have to connect to the game
        and generate a new one time token to get their verification role
        """
        tgdb = self.get_tgdb()

        message = await ctx.send("Finding out the ckey of user....")
        async with ctx.typing():
            # Attempt to find the discord link from the user
            discord_link = await tgdb.discord_link_for_discord_id(ctx, discord_user.id)
            if discord_link:
                # now clear all the links for this ckey
                await tgdb.clear_all_valid_discord_links_for_ckey(ctx, discord_link.ckey)
                message = await message.edit(content=f"User has been devalidated")
            else:
                message = await message.edit(content=f"This discord user has no ckey linked")

    #Now the only user facing command, so this has rate limiting across the sky
    @commands.cooldown(2, 60, type=commands.BucketType.user)
    @commands.cooldown(6, 60, type=commands.BucketType.guild)
    @commands.max_concurrency(3, per=commands.BucketType.guild, wait=False)
    @commands.guild_only()
    @commands.command()
    async def verify(self, ctx, *, one_time_token: str = None):
        """
        Attempt to verify the user, based on the passed in one time code
        This command is rated limited to two attempts per user every 60 seconds, and 6 attempts per entire discord every 60 seconds
        """
        #Get the minimum required living minutes
        min_required_living_minutes = await self.config.guild(ctx.guild).min_living_minutes()
        instructions_link = await self.config.guild(ctx.guild).instructions_link()
        role = await self.config.guild(ctx.guild).verified_role()
        verified_role = await self.config.guild(ctx.guild).verified_living_role()
        role = ctx.guild.get_role(role)
        verified_role = ctx.guild.get_role(verified_role)
        tgdb = self.get_tgdb()
        ckey = None

        # First lets try to remove their message, since the one time token is technically a secret if something goes wrong
        try:
            await ctx.message.delete()
        except(discord.DiscordException):
            await ctx.send("I do not have the required permissions to delete messages, please remove/edit the one time token manually.")
        if not role:
            raise TGUnrecoverableError("No verification role is configured, configure it with the config command")
        if not verified_role:
            raise TGUnrecoverableError("No verification role is configured for living minutes, configure it with config command")

        if role and verified_role in ctx.author.roles:
            return await ctx.send("You already are verified")

        message = await ctx.send("Attempting to verify you....")
        async with ctx.typing():

            if one_time_token:
                # Attempt to find the user based on the one time token passed in.
                ckey = await tgdb.lookup_ckey_by_token(ctx, one_time_token)

            # they haven't specified a one time token or it didn't match, see if we already have a linked ckey for the user id that is still valid
            if ckey is None:
                discord_link = await tgdb.discord_link_for_discord_id(ctx, ctx.author.id)
                if(discord_link and discord_link.valid > 0):
                    # Now look for the user based on the ckey
                    player = await tgdb.get_player_by_ckey(ctx, discord_link.ckey)
                    if player and player['living_time'] >= min_required_living_minutes:
                        await ctx.author.add_roles(verified_role, reason="User has verified against their in game living minutes")
                    # we have a fast path, just reapply the linked role and bail
                    await ctx.author.add_roles(role, reason="User has verified in game")
                    return await message.edit(content=f"Congrats {ctx.author} your verification is complete")

                raise TGRecoverableError(f"Sorry {ctx.author} it looks like we don't recognise this one use token or it has expired or you don't have a ckey linked to this discord account, go back into game and try generating one another! See {instructions_link} for more information. \n\nIf it's still failing after a few tries, ask for support from the verification team, ")

            log.info(f"Verification request by {ctx.author.id}, for ckey {ckey}")
            # Now look for the user based on the ckey
            player = await tgdb.get_player_by_ckey(ctx, ckey)

            if player is None:
                raise TGRecoverableError(f"Sorry {ctx.author} looks like we couldn't look up your user, ask the verification team for support!")

            # clear any/all previous valid links for ckey or the discord id (in case they have decided to make a new ckey)
            await tgdb.clear_all_valid_discord_links_for_ckey(ctx, ckey)
            await tgdb.clear_all_valid_discord_links_for_discord_id(ctx, ctx.author.id)
            # Record that the user is linked against a discord id
            await tgdb.update_discord_link(ctx, one_time_token, ctx.author.id)
            if role:
                await ctx.author.add_roles(role, reason="User has verified in game")
            if player['living_time'] >= min_required_living_minutes:
                await ctx.author.add_roles(verified_role, reason="User has verified against their in game living minutes")
            return await message.edit(content=f"Congrats {ctx.author} your verification is complete", color=0xff0000)

    @verify.error
    async def verify_error(self, ctx, error):
        # Our custom, something recoverable went wrong error type
        if isinstance(error, TGRecoverableError):
            embed=discord.Embed(title=f"Error attempting to verify you:", description=f"{format(error)}", color=0xff0000)
            await ctx.send(content=f"", embed=embed)

        elif isinstance(error, commands.MaxConcurrencyReached):
            embed=discord.Embed(title=f"There are too many verifications in process, try again in 30 seconds:", description=f"{format(error)}", color=0xff0000)
            await ctx.send(content=f"", embed=embed)
            log.exception(f"Too many users attempting to verify concurrently, db wait hit?")

        elif isinstance(error, commands.CommandOnCooldown):
            embed=discord.Embed(title=f"Hey slow down buddy:", description=f"{format(error)}", color=0xff0000)
            await ctx.send(content=f"", embed=embed)
            log.warning(f"Verification limit hit, user is being bad {ctx.author}, discord id {ctx.author.id}")

        elif isinstance(error, commands.NoPrivateMessage):
            embed=discord.Embed(title=f"Wrong channel, bud, leather club is 3 blocks down:", description=f"{format(error)}", color=0xff0000)
            await ctx.send(content=f"", embed=embed)
        else:
            # Something went badly wrong, log to the console
            log.exception("Internal error while verifying a user")
            # now pretend everything is fine to the user :>
            embed=discord.Embed(title=f"System error occurred", description=f"Contact the server admins for assistance", color=0xff0000)
            await ctx.send(content=f"", embed=embed)

    @tgverify.command()
    async def test(self, ctx, discord_user: discord.User):
        """
        Test welcome message sending
        """
        guild = ctx.guild
        member = guild.get_member(discord_user.id)
        await self.handle_member_join(member)
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        await self.handle_member_join(member)

    async def handle_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        if guild is None:
            return
        channel_id = await self.config.guild(guild).welcomechannel()
        channel = cast(discord.TextChannel, guild.get_channel(channel_id))
        if channel is None:
            log.info(f"tgverify channel not found for guild, it was probably deleted User joined: {member}")
            return
        
        if not guild.me.permissions_in(channel).send_messages:
            log.info(f"Permissions Error. User that joined:{member}")
            log.info(f"Bot doesn't have permissions to send messages to {guild.name}'s #{channel.name} channel")
            return
        
        final = ""
        if await self.config.guild(guild).disabled():
            msg = await self.config.guild(guild).disabledgreeting()
            final = msg.format(member, guild)
        else:
            msg = await self.config.guild(guild).welcomegreeting()
            final = msg.format(member, guild)
        bunkermsg = await self.config.guild(guild).bunkerwarning()
        bunker = await self.config.guild(guild).bunker()
        if bunkermsg != "" and bunker:
            final = final + " " + bunkermsg
        
        await channel.send(final)
    
    def get_tgdb(self):
        tgdb = self.bot.get_cog("TGDB")
        if not tgdb:
            raise TGUnrecoverableError("TGDB must exist and be configured for tgverify cog to work")

        return tgdb
