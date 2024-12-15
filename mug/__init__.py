from .mug import Mug

async def setup(bot):
    await bot.add_cog(Mug(bot))