from .coderbusfyi import CoderBusFYI


async def setup(bot):
    await bot.add_cog(CoderBusFYI(bot))
