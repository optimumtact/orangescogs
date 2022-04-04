from .gbp import gbp


def setup(bot):
    bot.add_cog(gbp(bot))
