from .gbp import gbp


async def setup(bot):
    await bot.add_cog(gbp(bot))
