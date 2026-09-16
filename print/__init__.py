from .print import PrintCog


async def setup(bot):
    await bot.add_cog(PrintCog(bot))
