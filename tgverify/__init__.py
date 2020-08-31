from .tgverify import TGverify

def setup(bot):
    bot.add_cog(TGverify(bot))