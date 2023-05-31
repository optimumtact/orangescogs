from .based import Based

async def setup(bot):
    await bot.add_cog(Based(bot))
