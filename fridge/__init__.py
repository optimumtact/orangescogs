from .fridge import Fridge

def setup(bot):
    bot.add_cog(Fridge(bot))
