from .timeout import Timeout

async def setup(bot):
    await bot.add_cog(Timeout(bot))
