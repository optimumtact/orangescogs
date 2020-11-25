#Standard Imports
import logging
from typing import Union

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

from typing import cast

__version__ = "1.1.0"
__author__ = "oranges"

log = logging.getLogger("red.oranges_fridge")

BaseCog = getattr(commands, "Cog", object)

class Fridge(BaseCog):
    """
    Add stuff to the fridge
    """
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=672261474290237490, force_registration=True)
        default_guild = {
            "fridge": None,
        }
        self.config.register_guild(**default_guild)

    @commands.guild_only()
    @commands.group()
    async def fridge(self,ctx):
        """
        Fridge commands
        """
        pass


    @fridge.command()
    async def current(self, ctx):
        """
        Who is currently on the fridge
        """
        user = await self.config.guild(ctx.guild).fridge()
        await ctx.send(f"{user} is currently on top of the fridge")

    @fridge.command()
    async def put(self, ctx, member: discord.Member):
        """
        Put this person on the fridge
        """
        user = await self.config.guild(ctx.guild).fridge.set(member.mention)
        await ctx.send(f"{member.mention} has been put on top of the fridge")
