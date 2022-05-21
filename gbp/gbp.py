import requests
import os.path

from redbot.core import commands, utils, Config

__version__ = "1.0.0"
__author__ = "SuperNovaa41"

BaseCog = getattr(commands, "Cog", object)


class gbp(BaseCog):
    """
    Find your GBP
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=672261474290237490, force_registration=True)

        default_global = {
            "gbp": {}
        }
        self.config.register_global(**default_global)

    async def get_latest_gbp(self):
        response = requests.get(
            url="https://raw.githubusercontent.com/tgstation/tgstation/gbp-balances/.github/gbp-balances.toml"
            )
        content = response.text

        raw_lines = []
        line = ""
        for char in content:  # first we cleanse the garbage lines
            line += char
            if char == '\n':
                if (ord(line[0]) >= ord('0') and ord(line[0]) <= ord('9')):
                    raw_lines.append(line)
                line = ""
        pairs = []
        for line in raw_lines:
            segments = line.split(" ")
            if segments[-1][-1:] == '\n':
                segments[-1] = segments[-1][:-1]
            pairs.append([int(segments[2]), segments[-1]])
        for n in range(len(pairs)-1, 0, -1):
            for i in range(n):
                if pairs[i][0] < pairs[i + 1][0]:
                    pairs[i][1], pairs[i+1][1] = pairs[i+1][1], pairs[i][1]
                    pairs[i][0], pairs[i+1][0] = pairs[i+1][0], pairs[i][0]

        final_dict = {}
        i = 1
        for pair in pairs:
            final_dict[i] = (pair[1], pair[0])
            i += 1
        await self.config.gbp.set(final_dict)

    @commands.command()
    async def fetchgbp(self, ctx):
        await self.get_latest_gbp()
        await ctx.send("Fetched latest GBP!")

    @commands.command()
    async def findname(self, ctx, name=""):
        msg = ""
        gbp_dict = await self.config.gbp()
        for i in range(1, len(gbp_dict) + 1):
            line = gbp_dict[str(i)]
            if name.lower() in line[0].lower():
                msg += "#" + str(i) + ": " + gbp_dict[str(i)][0] + " (" + str(gbp_dict[str(i)][1]) + " GBP)\n"
        if (msg == ""):
            await ctx.send("No user found!")
            return
        if (len(msg) >= 2000):
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send(f"```{msg}```")

    @commands.command()
    async def findpos(self, ctx, pos):
        gbp_dict = await self.config.gbp()
        if pos in gbp_dict:
            await ctx.send(f"```#{pos}: {gbp_dict[pos][0]} ({gbp_dict[pos][1]} GBP)```")
            return
        await ctx.send("No user at that position!")

    @commands.command()
    async def findgbp(self, ctx, gbp_to_find):
        msg = ""
        gbp_dict = await self.config.gbp()
        for i in range(1, len(gbp_dict) + 1):
            line = gbp_dict[str(i)]
            if gbp_to_find == str(line[1]):
                msg += "#" + str(i) + ": " + gbp_dict[str(i)][0] + " (" + str(gbp_dict[str(i)][1]) + " GBP)\n"
        if (msg == ""):
            await ctx.send("No user found with this GBP!")
            return
        if (len(msg) >= 2000):
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send(f"```{msg}```")

    @commands.command()
    async def finduntil(self, ctx, up_to_pos):
        msg = ""
        gbp_dict = await self.config.gbp()
        for i in range(1, len(gbp_dict) + 1):
            if int(up_to_pos) < i:
                break
            msg += "#" + str(i) + ": " + gbp_dict[str(i)][0] + " (" + str(gbp_dict[str(i)][1]) + " GBP)\n"
        if (msg == ""):
            await ctx.send("An error has occured!")
            return
        if (len(msg) >= 2000):
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send(f"```{msg}```")
    
    @commands..command()
    async def totalgbp(self, ctx):
        total_pos_gbp = 0
        total_neg_gbp = 0
        gbp_dict = await self.config.gbp()
        for i in range(1, len(gbp_dict) + 1):
            current_gbp = int(gbp_dict[str(i)][1])
            if current_gbp > 0:
                total_pos_gbp += current_gbp
            else:
                total_neg_gbp += abs(current_gbp)
        await ctx.send(f"```There is {total_pos_gbp} positive GBP, and {total_neg_gbp} negative GBP in circulation.")

