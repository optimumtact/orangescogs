import logging

import requests
from fuzzywuzzy import process
from redbot.core import Config, commands, utils
from tomlkit import loads, parse

__version__ = "1.0.0"
__author__ = "SuperNovaa41"

BaseCog = getattr(commands, "Cog", object)

log = logging.getLogger("red.oranges_gbp")


class gbp(BaseCog):
    """
    Find your GBP
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=672261474290237490, force_registration=True
        )
        self.usertogbp = dict()
        self.postouser = dict()
        self.usertopos = dict()

        default_global = {"gbp": {}}
        self.config.register_global(**default_global)

    @commands.guild_only()
    @commands.group()
    async def gbp(self, ctx):
        """
        gbp commands group
        """
        pass

    async def get_latest_gbp(self):
        response = requests.get(
            url="https://raw.githubusercontent.com/tgstation/tgstation/gbp-balances/.github/gbp-balances.toml",
        )
        content = response.text
        document = parse(content)
        gbptouser = []
        for githubid, gbp in document.items():
            user = gbp.trivia.comment.strip("# ")
            gbptouser.append((user, gbp))
            self.usertogbp[user] = gbp

        # Sort by GBP value count
        gbptouser.sort(key=lambda x: x[1], reverse=True)

        # index user to position
        for index, item in enumerate(gbptouser):
            index = index + 1  # count like a human
            user, gbp = item
            self.postouser[index] = user
            self.usertopos[user] = index

    @gbp.command()
    async def find(self, ctx, name=""):
        await self.get_latest_gbp()
        msg = ""
        choices = process.extract(name, self.usertogbp.keys(), limit=10)
        for name, ratio in choices:
            if ratio >= 90:
                gbp = self.usertogbp[name]
                pos = self.usertopos[name]
                msg += f"#{pos}: {name} - {gbp}\n"
        if msg == "":
            await ctx.send("No user found!")
            return
        else:
            await ctx.send(f"```{msg}```")

    @gbp.command()
    async def at(self, ctx, pos: int):
        await self.get_latest_gbp()
        if pos in self.postouser:
            user = self.postouser[pos]
            await ctx.send(f"#{pos}: {user} - {self.usertogbp[user]}")
            return
        await ctx.send("No user at that position!")

    @gbp.command()
    async def top(self, ctx, up_to_pos: int):
        await self.get_latest_gbp()
        msg = ""
        for index, data in enumerate(self.postouser.items()):
            if index == up_to_pos:
                break
            position, user = data
            msg += f"#{position} - {user}, {self.usertogbp[user]}\n"
        if len(msg) >= 2000:
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send(f"```{msg}```")

    @gbp.command()
    async def totals(self, ctx):
        await self.get_latest_gbp()
        total_pos_gbp = 0
        total_neg_gbp = 0
        for user, current_gbp in self.usertogbp.items():
            if current_gbp > 0:
                total_pos_gbp += current_gbp
            else:
                total_neg_gbp += abs(current_gbp)
        await ctx.send(
            f"```There is {total_pos_gbp} positive GBP, and {total_neg_gbp} negative GBP in circulation.```"
        )

    @gbp.command(aliases=["points"])
    async def costs(self, ctx):
        response = requests.get(
            url="https://raw.githubusercontent.com/tgstation/tgstation/master/.github/gbp.toml"
        )
        content = response.text
        result = loads(content)
        msg = ""
        for label, cost in result["points"].items():
            msg += f"{label} = {cost}\n"

        await ctx.send(msg)
