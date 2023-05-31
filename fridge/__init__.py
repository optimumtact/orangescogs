from .fridge import Fridge

async def setup(bot):
    await bot.add_cog(Fridge(bot))
