from .gbp import GBP

def setup(bot):
    bot.add_cog(GBP(bot))
