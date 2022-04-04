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

    def get_latest_gbp(self):
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

        with open("gbp.txt", 'w') as file:
            i = 1
            for pair in pairs:
                file.write(
                    "#" + str(i) + ": " + pair[1] + " (" + str(pair[0]) + " GBP)\n"
                )
                i += 1

    @commands.command()
    async def fetchgbp(self, ctx):
        self.get_latest_gbp()
        await ctx.send("Fetched latest GBP!")

    @commands.command()
    async def findname(self, ctx, name=""):
        self.does_file_exist()
        msg = ""
        with open("gbp.txt", 'r') as file:
            lines = file.readlines()
            for line in lines:
                if name.lower() in line.lower():
                    msg += line
        if (msg == ""):
            await ctx.send("No user found!")
            return
        if (len(msg) >= 2000):
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send("```" + msg + "```")

    @commands.command()
    async def findpos(self, ctx, pos):
        self.does_file_exist()
        with open("gbp.txt", 'r') as file:
            lines = file.readlines()
            for line in lines:
                num = line.split(" ")[0]
                if num[1:-1] == pos:
                    await ctx.send("```" + line + "```")
                    return
        await ctx.send("No user at that position!")

    @commands.command()
    async def findgbp(self, ctx, gbp_to_find):
        self.does_file_exist()
        msg = ""
        with open("gbp.txt", 'r') as file:
            lines = file.readlines()
            for line in lines:
                gbp = line.split(" ")[2]
                if gbp[1:] == gbp_to_find:
                    msg += line
        if (msg == ""):
            await ctx.send("No user found with this GBP!")
            return
        if (len(msg) >= 2000):
            await ctx.send(file=utils.chat_formatting.text_to_file(msg, "gbp.txt"))
        else:
            await ctx.send("```" + msg + "```")

    def does_file_exist(self):
        if not os.path.exists("gbp.txt"):
            self.get_latest_gbp()
