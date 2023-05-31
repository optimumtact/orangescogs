from .tgverify import TGverify

async def setup(bot):
    await bot.add_cog(TGverify(bot))
