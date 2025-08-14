from .animals import Animals


async def setup(bot):
    await bot.add_cog(Animals(bot))
