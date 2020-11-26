#Standard Imports
import logging
import random
from typing import Union

#Discord Imports
import discord

#Redbot Imports
from redbot.core import commands, checks, Config

from typing import cast
import json
from pathlib import Path

from collections import Counter, defaultdict


from redbot.core.data_manager import cog_data_path

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
            "items": ["Banana", "Milk", "Bread", "Butter", "Chocolate", "Chocolate Milk", "Brussel sprouts, yuck!!", "A half eaten ham sandwich"],
        }
        self.config.register_guild(**default_guild)
        self.fridges = defaultdict(Counter)


        datapath = cog_data_path(self)
        for guild in self.bot.guilds:
            filename = Path(datapath, f"{guild.id}.json")
            if filename.exists()
                log.info(f"Loading backing store {filename}")
                with open(filename, 'r') as backingstore:
                    storeditems = json.load(backingstore)
                    fridge = self.fridges[guild]
                    for item in storeditems:
                        fridge[item] +=1

    
    def cog_unload(self):
        datapath = cog_data_path(self)
        for guild in self.fridges.keys():
            fridge = self.fridges[guild]
            storeditems = list()
            for key in fridge.keys():
                count = fridge[key]
                for _ in range(count):
                    storeditems.append(key)
            filename = Path(datapath, f"{guild.id}.json")
            
            log.info(f"Writing backing store {filename}")
            with open(filename, 'w') as backingstore:
                json.dump(storeditems, backingstore)

        log.info("Unloading")

    @commands.guild_only()
    @commands.group()
    async def fridge(self,ctx):
        """
        Fridge commands
        """
        pass
    
    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @fridge.group()
    async def buyables(self,ctx):
        """
        Buyable item commands
        """
        pass

    @fridge.command(aliases=['check'])
    async def current(self, ctx):
        """
        Who is currently on the fridge
        """
        user = await self.config.guild(ctx.guild).fridge()
        if user:
            await ctx.send(f"{user} is currently on top of the fridge")
        else:
            await ctx.send(f"You look up on the top of the fridge but there is only dust")

    @fridge.command()
    async def put(self, ctx, member: discord.Member):
        """
        Put this person on the fridge
        """
        user = await self.config.guild(ctx.guild).fridge.set(member.name)
        await ctx.send(f"{member.mention} has been put on top of the fridge")

    @fridge.command()
    async def add(self, ctx, *, item):
        """
        Put something in the fridge
        """
        if("@" in item):
            await ctx.send(f"Nice try")    
            return
        
        if(len(item) > 100):
            await ctx.send(f"This is too big to fit in the fridge")    
            return
        
        if(item.count('\n') > 5):
            await ctx.send(f"This is too spammy to fit in the fridge")
            return

        fridge = self.fridges[ctx.guild]
        fridge[item]+=1
        await ctx.send(f"You put {item} in the fridge")

        items = await self.config.guild(ctx.guild).items()
        if item not in items:
            items.append(item)
            items = await self.config.guild(ctx.guild).items.set(items)

    @fridge.command(aliases=['take', 'remove', 'find', 'eat'])
    async def get(self, ctx):
        """
        Get a random item out of the fridge
        """
        fridge = self.fridges[ctx.guild]
        if(len(fridge) <= 0):
            await ctx.send(f"There's nothing in the fridge, you should use restock to refill it!")
            return

        item = random.choice(list(fridge.keys()))
        fridge[item] -= 1
        if fridge[item] <= 0:
            del(fridge[item])
            await ctx.send(f"You take the last {item}, enjoy!")
            return

        await ctx.send(f"You take out {item}, enjoy!")


    @fridge.command()
    async def peek(self, ctx):
        """
        Peek into the fridge
        """
        fridge = self.fridges[ctx.guild]
        items = fridge.keys()
        if(len(items) <= 0):
            await ctx.send(f"Bored, you open your fridge only to find there's nothing there!, use restock to refill your fridge")
            return

        sample = min(10, len(items))
        spotted = random.sample(items, sample)
        output = list()
        for item in spotted:
            if fridge[item] > 1:
                output.append("{0} {1}".format(fridge[item], item))
            else
                output.append(f"The last {item}")
        await ctx.send(f"Bored, you open your fridge and stare into it for a few minutes and you see: {', '.join(output)}")

    @fridge.command()
    async def restock(self, ctx, amount=100):
        """
        Refill your fridge with a shopping session
        """
        items = list(set(await self.config.guild(ctx.guild).items()))
        fridge = self.fridges[ctx.guild]
        for _ in range(amount):
            fridge[random.choice(items)]+=1

        await ctx.send(f"You had a productive shopping session and the fridge is now teeming with items")


    @fridge.command()
    async def tip(self, ctx):
        message = f"Holy shit {ctx.author.mention} just straight up tipped the fridge over, all the items spilled out!"
        user = await self.config.guild(ctx.guild).fridge()
        if user:
            message += f" {user} is sent flying from the top of the fridge"
        self.fridges[ctx.guild] = Counter()
        await self.config.guild(ctx.guild).fridge.set(None)
        await ctx.send(message)

    @buyables.command()
    async def remove(self, ctx,  *, item):
        """
        Remove an item from the buyable store
        """
        items = await self.config.guild(ctx.guild).items()
        if item in items:
            items.remove(item)
            items = await self.config.guild(ctx.guild).items.set(items)
            await ctx.send(f"{item} has been removed from the Buyables")


    @buyables.command()
    @checks.mod_or_permissions(administrator=True)
    async def clear(self, ctx):
        """
        Clear all buyable items
        """
        self.fridges[ctx.guild] = Counter()
    
        await self.config.guild(ctx.guild).items.set(["Banana", "Milk", "Milk", "Bread", "Butter", "Chocolate", "Chocolate Milk", "Brussel sprouts, yuck!!", "A half eaten ham sandwich"])
        await ctx.send(f"Buyables has been cleared")

    @buyables.command()
    @checks.mod_or_permissions(administrator=True)
    async def deduplicate(self, ctx):
        """
        Remove duplicate buyable items added in earlier versions
        """
        items = await self.config.guild(ctx.guild).items()
        setitems = set(items)
        final = list(setitems)    
        items = await self.config.guild(ctx.guild).items.set(final)
        await ctx.send(f"Buyables deduplicated")
    
    
    @buyables.command()
    @checks.mod_or_permissions(administrator=True)
    async def dump(self, ctx):
        """
        Dump all buyables, inadvisable to use in normal circumstances
        """
        items = await self.config.guild(ctx.guild).items()
        await ctx.send(",".join(items))