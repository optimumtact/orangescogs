from .codebases import CodeBases

async def setup(bot):
    await bot.add_cog(CodeBases(bot))
