from .pets import Pets

async def setup(bot):
    await bot.add_cog(Pets(bot))
