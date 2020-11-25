#Standard Imports
import logging
import random
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
            "items": ["Banana", "Milk", "Bread", "Butter", "Chocolate", "Chocolate Milk", "Brussel sprouts, yuck!!", "A half eaten ham sandwich"]
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

    @fridge.command()
    async def add(self, ctx, *, item):
        """
        Put something in the fridge
        """
        if("@" in item):
            await ctx.send(f"Nice try")    
            return
        items = await self.config.guild(ctx.guild).items()
        item = item.replace('@', '@​\u200b') 
        items.append(item)
        items = await self.config.guild(ctx.guild).items.set(items)
        await ctx.send(f"You put {item} in the fridge")

    @fridge.command()
    async def get(self, ctx):
        """
        Get a random item out of the fridge
        """
        items = await self.config.guild(ctx.guild).items()
        item = random.choice(items)
        await ctx.send(f"You got an {item}")

    @fridge.command()
    async def peek(self, ctx):
        """
        Peek into the fridge
        """
        items = await self.config.guild(ctx.guild).items()
        sample = min(30, len(items))
        spotted = random.sample(items, sample)
        await ctx.send(f"Bored, you open your fridge and stare into it for a few minutes and you see: {', '.join(items)}")

    @fridge.command()
    @checks.mod_or_permissions(administrator=True)
    async def remove(self, ctx,  *, item):
        """
        Remove an item from the fridge
        """
        items = await self.config.guild(ctx.guild).items()
        if item in items:
            items.remove(item)
            items = await self.config.guild(ctx.guild).items.set(items)
            await ctx.send(f"{item} has been removed from the fridge")


    @fridge.command()
    @checks.mod_or_permissions(administrator=True)
    async def clear(self, ctx):
        """
        Clear all items
        """
        await self.config.guild(ctx.guild).items.set(["Banana", "Milk", "Bread", "Butter", "Chocolate", "Chocolate Milk", "Brussel sprouts, yuck!!", "A half eaten ham sandwich"])
        await ctx.send(f"Fridge has been cleared")
