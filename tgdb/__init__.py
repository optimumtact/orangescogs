from .tgdb import TGDB

async def setup(bot):
    await bot.add_cog(TGDB(bot))
