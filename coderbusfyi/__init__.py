from .coderbusfyi import CoderBusFYI


async def setup(bot):
    cog = CoderBusFYI(bot)
    await bot.add_cog(cog)
    await cog.initialize()
