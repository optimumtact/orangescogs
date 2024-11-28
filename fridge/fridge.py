# Standard Imports
import datetime
import json
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Union, cast

# Discord Imports
import discord
from fuzzywuzzy import process

# Redbot Imports
from redbot.core import Config, checks, commands
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
        # format: "You look up on the top of the fridge but there is only some {fridge_trash} up there."
        self.fridge_trash = [
            "blood",
            "cat hair",
            "copies of spore: galactic adventures",
            "cult runes",
            "dirt",
            "dust",
            "entropy",
            "false promises",
            "garlic",
            "muddle puddle tweetle poodle beetle noodle bottle paddle battle (when beetles fight these battles \
            in a bottle with their paddles and the bottle's on a poodle and the poodle's eating noodles)",
            "of the fine china",
            "of the tiny aliens from men in black",
            "old bread",
            "rafter assistants",
            "sadness",
            "space ants",
        ]
        self.reactions = [
          "how cruel!",
          "zesty!",
          "yummers!",
          "enjoy!",
          "tasty!",
          "crunchy!",
          "nutritious!",
          "gross!",
          "that was fucked up!",
          "avert your eyes!",
          "why would you do that?",
          "bada bing!",
          "how nostalgic!",
          "just like mother used to make!",
          "god help us all!",
        ]
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        default_guild = {
            "fridge": None,
            "fridgetime": None,
            "bracers_dict": {},
            "max_bracers": 3,
            "temperature": -10,
            "items": [
                "Banana",
                "Milk",
                "Bread",
                "Butter",
                "Chocolate",
                "Chocolate Milk",
                "Brussel sprouts, yuck!!",
                "A half eaten ham sandwich",
            ],
        }
        self.config.register_guild(**default_guild)
        self.fridges = defaultdict(Counter)

        datapath = cog_data_path(self)
        for guild in self.bot.guilds:
            filename = Path(datapath, f"{guild.id}.json")
            if filename.exists():
                log.info(f"Loading backing store {filename}")
                with open(filename, "r") as backingstore:
                    storeditems = json.load(backingstore)
                    fridge = self.fridges[guild]
                    for item in storeditems:
                        fridge[item] += 1

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
            with open(filename, "w") as backingstore:
                json.dump(storeditems, backingstore)

        log.info("Unloading")

    @commands.guild_only()
    @commands.group()
    async def fridge(self, ctx):
        """
        Fridge commands
        """
        pass

    @commands.guild_only()
    @checks.mod_or_permissions(administrator=True)
    @fridge.group()
    async def buyables(self, ctx):
        """
        Buyable item commands
        """
        pass

    @commands.cooldown(1, 300, type=commands.BucketType.user)
    @fridge.command(aliases=["support"])
    async def brace(self, ctx):
        """
        Support the fridge against tippers
        """
        member = ctx.author
        async with self.config.guild(ctx.guild).bracers_dict() as bracers:
            if str(member.id) in bracers:
                await ctx.send("You are already stuck between the wall and the fridge!")
                return None
            if len(bracers) >= await self.config.guild(ctx.guild).max_bracers():
                await ctx.send(
                    "There's already too many people stuck between the wall and the fridge!"
                )
                return None
            message = f"{member.mention} wedges themselves between the wall and the fridge, bracing it upright."
            bracers[str(member.id)] = member.name
        await ctx.send(message)
        return None

    @fridge.command(aliases=["check"])
    async def current(self, ctx):
        """
        Who is currently on the fridge
        """
        user = await self.config.guild(ctx.guild).fridge()
        if not user:
            await ctx.send(
                f"You look up on the top of the fridge but there is only some {random.choice(self.fridge_trash)} up there."
            )
            return
        usurpation_isoformat = await self.config.guild(ctx.guild).fridgetime()
        # convert to date object and then subtract it from another date object to get a timedelta object. must be now - date to get a positive delta value
        usurpation_timedelta = (
            datetime.datetime.now().date()
            - datetime.date.fromisoformat(usurpation_isoformat)
        )
        reign_blurb = ""
        time_blurb = " They've been up there for "
        if not usurpation_timedelta.days:
            time_blurb += "less than a day."
        else:
            time_blurb += f"{usurpation_timedelta.days} days."
        # one month of rule (roughly)
        if usurpation_timedelta.days > 30:
            reign_blurb = f" Their reign has been long. Fridge historians will write about how {user} put a temporary pause on all the fridge tipping chaos."
        await ctx.send(
            f"{user} is currently on top of the fridge.{time_blurb}{reign_blurb}"
        )

    @fridge.command()
    async def put(self, ctx, member: discord.Member):
        """
        Put this person on the fridge
        """
        if member == ctx.author:
            await ctx.send(f"You can't reach the top of the fridge by YOURSELF.")
            return
        fridge_incumbent = await self.config.guild(ctx.guild).fridge()
        if member.name == fridge_incumbent:
            await ctx.send(f"{fridge_incumbent} is already on top of the fridge!")
            return
        message = "ERROR!"
        # we want a string for saving it as data, and we only care about the day they began their rule
        time = str(datetime.datetime.now().date())
        if fridge_incumbent:
            message = f"{fridge_incumbent} has been USURPED from the fridge by {member.name} on {time}!"
        else:
            message = f"{member.mention} has been put on top of the fridge on {time}."
        await self.config.guild(ctx.guild).fridgetime.set(time)
        await self.config.guild(ctx.guild).fridge.set(member.name)
        await ctx.send(message)

    @fridge.command()
    async def add(self, ctx, *, item):
        """
        Put something in the fridge
        """
        if "@" in item:
            await ctx.send(f"Nice try")
            return

        if len(item) > 100:
            await ctx.send(f"This is too big to fit in the fridge")
            return

        if item.count("\n") > 5 or "```" in item:
            await ctx.send(f"This is too spammy to fit in the fridge")
            return

        fridge = self.fridges[ctx.guild]
        fridge[item] += 1
        await ctx.send(f"You put {item} in the fridge")

        config = self.config.guild(ctx.guild)
        async with config.items() as items:
            if item not in items:
                items.append(item)
        log.info(f"User {ctx.author.id} put {item} in the fridge")

    @fridge.command(aliases=[])
    async def feed(self, ctx, *, member: discord.Member):
        """
        feed your friends the concrete pills 
        """
        item = await self._get(ctx, None)
        if (item):
            await ctx.send(f"You feed {member.mention} {item}, {random.choice(self.reactions)}")

    @fridge.command(aliases=[])
    async def yummers(self, ctx, *, search=None):
        """
        I see you got the extra whipped cream in there, huh?
        """
        item = await self._get(ctx, search)
        if (item):
            await ctx.send(f"You take out {item}, yummers!")

    @fridge.command(aliases=["take", "remove", "find", "eat"])
    async def get(self, ctx, *, search=None):
        """
        Get a random item out of the fridge
        """
        item = await self._get(ctx, search)
        if (item):
            await ctx.send(f"You take out {item}, enjoy!")

    async def _get(self, ctx, search):
        fridge = self.fridges[ctx.guild]
        if len(fridge) <= 0:
            await ctx.send(
                f"There's nothing in the fridge, you should use restock to refill it!"
            )
            return None

        if search:
            item = process.extractOne(search, list(fridge.keys()), score_cutoff=80)
            if not item:
                await ctx.send(
                    f"You don't seem to have anything you want, maybe get some and add?"
                )
                return None
            item = item[0]

        else:
            item = random.choice(list(fridge.keys()))

        fridge[item] -= 1
        if fridge[item] <= 0:
            del fridge[item]
            return f"the last {item}"

        return item

    @fridge.command()
    async def peek(self, ctx, *, search=None):
        """
        Peek into the fridge, specify a search to find certain types of items
        """
        chill_message = ""
        current_temperature = await self.config.guild(ctx.guild).temperature()
        if current_temperature in range(-10, 1):
            chill_message = ", it doesn't feel as chilly as you expected"
        if current_temperature in range(0, 9):
            chill_message = ", its rather warm in here"
        if current_temperature >= 10:
            chill_message = ", why is it so hot in the fridge!"
        if current_temperature <= -10:
            chill_message = ", the cool air feels nice against your face"

        fridge = self.fridges[ctx.guild]
        items = list(fridge.keys())
        if len(items) <= 0:
            await ctx.send(
                f"Bored, you open your fridge only to find there's nothing there!, use restock to refill your fridge{chill_message}"
            )
            return

        spotted = list()
        if search:
            fuzzy_matches = process.extract(search, items, limit=30)
            for match in fuzzy_matches:
                if match[1] > 80:
                    spotted.append(match[0])
        else:
            sample = min(10, len(items))
            spotted = random.sample(items, sample)

        if len(spotted) <= 0:
            await ctx.send(f"You couldn't really find anything like that")
            return

        output = list()

        for item in spotted:
            if fridge[item] > 1:
                output.append("{0} {1}".format(fridge[item], item))
            else:
                output.append(f"The last {item}")
        await ctx.send(
            f"Bored, you open your fridge and stare into it for a few minutes and you see: {', '.join(output)}{chill_message}"
        )

    @fridge.command()
    async def restock(self, ctx, amount=100):
        """
        Refill your fridge with a shopping session
        """
        items = list(set(await self.config.guild(ctx.guild).items()))
        fridge = self.fridges[ctx.guild]
        for _ in range(amount):
            fridge[random.choice(items)] += 1

        await ctx.send(
            f"You had a productive shopping session and the fridge is now teeming with items"
        )

    @commands.cooldown(1, 300, type=commands.BucketType.user)
    @fridge.command()
    async def tip(self, ctx):
        message = (
            f"Holy shit {ctx.author.mention} just straight up tipped the fridge over"
        )

        async with self.config.guild(ctx.guild).bracers_dict() as bracers:
            if len(bracers) > 0:
                brave_bracer = random.choice(tuple(bracers.keys()))
                message = f"{ctx.author.mention} charges at the fridge to tip it, but {bracers.pop(brave_bracer)} is bracing it against the wall and {ctx.author.mention} bounces off and gets knocked over, what a goober"
                await ctx.send(message)
                return None

        amount = random.randint(1, 10)
        fridge = self.fridges[ctx.guild]
        items = list(fridge.keys())
        sample = min(amount, len(items))
        spilled_out = random.sample(items, sample)
        if random.randrange(0, 100) < 60:
            await ctx.send("The temperature control blanks and shows an error code")
            # Resets the temperature gauge
            change = random.randint(-10, 10)
            await self.config.guild(ctx.guild).temperature.set(change)
        if len(spilled_out) >= 1:
            message += " items go flying everywhere!"
        else:
            message += " but nothing came out, lucky!"
        for spilled in spilled_out:

            lost = random.randint(1, fridge[spilled])
            if lost == 1:
                message += f" one {spilled} gets scattered across the floor,"
            else:
                message += f" {lost} {spilled} get scattered across the floor,"
            fridge[spilled] -= lost
            if fridge[spilled] <= 0:
                del fridge[spilled]
        user = await self.config.guild(ctx.guild).fridge()
        if user:
            message += f" {user} is sent flying from the top of the fridge."
        await self.config.guild(ctx.guild).fridge.set(None)
        await self.config.guild(ctx.guild).fridgetime.set(None)
        await ctx.send(message)
        return None

    @fridge.command(aliases=["cb"])
    @checks.mod_or_permissions(administrator=True)
    async def clear_bracers(self, ctx):
        """
        Removes all bracers from the fridge
        """
        await self.config.guild(ctx.guild).bracers_dict.set({})
        await ctx.send("All bracers removed.")

    @fridge.command(aliases=["smb"])
    @checks.mod_or_permissions(administrator=True)
    async def set_max_bracers(self, ctx, amount=3):
        """
        Removes all bracers from the fridge
        """
        await self.config.guild(ctx.guild).max_bracers.set(amount)
        await ctx.send(f"The maximum amount of bracers is now {amount}")

    @buyables.command()
    async def remove(self, ctx, *, item):
        """
        Remove an item from the buyable store
        """
        items = await self.config.guild(ctx.guild).items()
        if item in items:
            items.remove(item)
            items = await self.config.guild(ctx.guild).items.set(items)
            await ctx.send(f"{item} has been removed from the Buyables")

    @buyables.command()
    async def stats(self, ctx):
        """
        Get some stats on the fridgeg
        """
        items = await self.config.guild(ctx.guild).items()
        fridge = self.fridges[ctx.guild]
        current = len(fridge.keys())
        available = len(items)
        await ctx.send(
            f"There are currently {current} items in the fridge, with {available} items for sale in stores"
        )

    @buyables.command()
    @checks.mod_or_permissions(administrator=True)
    async def clear(self, ctx):
        """
        Clear all buyable items
        """
        self.fridges[ctx.guild] = Counter()

        await self.config.guild(ctx.guild).items.set(
            [
                "Banana",
                "Milk",
                "Milk",
                "Bread",
                "Butter",
                "Chocolate",
                "Chocolate Milk",
                "Brussel sprouts, yuck!!",
                "A half eaten ham sandwich",
            ]
        )
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
