from .tgdb import TGDB

def setup(bot):
    bot.add_cog(TGDB(bot))