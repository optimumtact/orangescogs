from .rolemanage import RoleManage


async def setup(bot):
    await bot.add_cog(RoleManage(bot))
