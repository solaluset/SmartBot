from discord import Member, User

from .i18n import t


async def can_operate(ctx, target: Member | User, action: str) -> bool:
    if target == ctx.author:
        await ctx.send(t("cant_operate.yourself", ctx.language, action=action))
        return False
    if target == ctx.me:
        await ctx.send(t("cant_operate.itself", ctx.language, action=action))
        return False
    if isinstance(target, Member):
        if target.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send(t("cant_operate.higher_role", ctx.language, action=action))
            return False
        if target == ctx.guild.owner:
            await ctx.send(t("cant_operate.owner", ctx.language, action=action))
            return False
        if target.top_role >= ctx.me.top_role:
            await ctx.send(t("cant_operate.member", ctx.language, action=action))
            return False
    return True
