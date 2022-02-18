from .timeout import Timeout

def setup(bot):
    bot.add_cog(Timeout(bot))
