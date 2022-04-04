from redbot.core import commands

__version__ = "1.0.0"
__author__ = "SuperNovaa41"

class GBP(BaseCog):
    """
    Find your GBP
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()    
    async def findname(self, ctx):
        await ctx.send("Test!")
    