#Standard Imports
import logging
from typing import Union

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

from tgcommon.errors import TGRecoverableError, TGUnrecoverableError
from tgcommon.util import normalise_to_ckey

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
        self.visible_config = ["min_living_minutes", "verified_role"]

        default_guild = {
            "min_living_minutes": 60,
            "verified_role": None,
            "instructions_link": ""
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
    @commands.group()
    @checks.mod_or_permissions(administrator=True)
    async def tgverify_config(self,ctx): 
        """
        SS13 Configure the settings on the verification cog
        """
        pass

    @tgverify_config.command()
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


    @tgverify_config.command()
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

    @tgverify_config.command()
    async def instructions_link(self, ctx, instruction_link: str):
        """
        Sets the link to further instructions on how to generate verification information
        """
        try:
            await self.config.guild(ctx.guild).instructions_link.set(instruction_link)
            await ctx.send(f"Instruction link set to: `{instruction_link}`")
        
        except (ValueError, KeyError, AttributeError):
            await ctx.send("There was a problem setting the instructions link")
    
    @tgverify_config.command()
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
            links = await tgdb.get_all_links_to_ckey(ctx, ckey)
            if len(links) <= 0:
                return await message.edit(content="No discord accounts found for this ckey")

            names = ""
            for link in links:
                names += f"User linked <@{link.discord_id}> on {link.timestamp}\n"

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
        role = ctx.guild.get_role(role)
        tgdb = self.get_tgdb()

        if not role:
            raise TGUnrecoverableError("No verification role is configured, configure it with .tgverify_config role")

        if role in ctx.author.roles:
            return await ctx.send("You already are verified")

        message = await ctx.send("Attempting to verify you....")
        async with ctx.typing():
            # First lets try to remove their message
            try:
                await ctx.message.delete()
            except(discord.DiscordException):
                await ctx.send("I do not have the required permissions to delete messages, please remove/edit the one time token manually.")
            
            if one_time_token:
                # Attempt to find the user based on the one time token passed in.
                ckey = await tgdb.lookup_ckey_by_token(ctx, one_time_token)
                
            # they haven't specified a one time token, see if we already have a linked ckey for them, that's valid as a fast path
            else:
                discord_link = await tgdb.discord_link_for_discord_id(ctx, ctx.author.id)
                if(discord_link and await tgdb.is_latest_link(ctx, discord_link)):
                    # we have a fast path, just reapply the linked role and bail
                    await ctx.author.add_roles(role, reason="User has verified against their in game living minutes")
                    return await message.edit(content=f"Congrats {ctx.author} your verification is complete")

                return await message.edit(content=f"You have not previously linked this account with our database so must generate a one time token to verify, see {instructions_link} for how you carry out this process")

            
            if ckey is None:
                raise TGRecoverableError(f"Sorry {ctx.author} it looks like we don't recognise this one use token or it has expired, go back into game and try generating one another! See {instructions_link} for more information. \n\nIf it's still failing after a few tries, ask for support from the verification team, ")
            
            log.info(f"Verification request by {ctx.author.id}, for ckey {ckey}")
            # Now look for the user based on the ckey
            player = await tgdb.get_player_by_ckey(ctx, ckey)
            
            if player is None:
                raise TGRecoverableError(f"Sorry {ctx.author} looks like we couldn't look up your user, ask the verification team for support!")

            if player['living_time'] <= min_required_living_minutes:
                return await message.edit(content=f"Sorry {ctx.author} you only have {player['living_time']} minutes as a living player on our servers, and you require at least {min_required_living_minutes}! You will need to play more on our servers to access all the discord channels, see {instructions_link} for more information")
    
            if role:
                await ctx.author.add_roles(role, reason="User has verified against their in game living minutes")


        # Record that the user is linked against a discord id
        await tgdb.update_discord_link(ctx, one_time_token, ctx.author.id)
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

        else:
            # Something went badly wrong, log to the console
            log.exception("Internal error while verifying a user")
            # now pretend everything is fine to the user :>
            embed=discord.Embed(title=f"System error occurred", description=f"Contact the server admins for assistance", color=0xff0000)
            await ctx.send(content=f"", embed=embed)

    def get_tgdb(self):
        tgdb = self.bot.get_cog("TGDB")
        if not tgdb:
            raise TGUnrecoverableError("TGDB must exist and be configured for tgverify cog to work")

        return tgdb
 