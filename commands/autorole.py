from discord.ext import commands
from modules import embed
from modules.i18n import t
from modules.prima import REMOVE_ALIASES
from modules.converters import ManageableRole


class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=("ar",), invoke_without_command=True)
    @commands.guild_only()
    async def autorole(self, ctx):
        "autorole.help"
        em = embed.Embed(ctx)
        role = await ctx.bot.get_guild_property(ctx.guild, "autorole")
        if role:
            role = ctx.guild.get_role(int(role))
        em.add_field(
            name=t("autorole.current", ctx.language),
            value=role.mention if role else t("autorole.not_set", ctx.language),
        )
        await em.send()

    @autorole.command(usage="autorole.set.usage")
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def set(self, ctx, role: ManageableRole):
        "autorole.set.help"
        await ctx.bot.guilds_data.upsert(
            guild_id=str(ctx.guild.id),
            autorole=str(role.id),
        )
        await ctx.send(t("autorole.set.set", ctx.language))

    @autorole.command(aliases=REMOVE_ALIASES)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def remove(self, ctx):
        "autorole.remove.help"
        await ctx.bot.guilds_data.upsert(
            guild_id=str(ctx.guild.id),
            autorole=None,
        )
        await ctx.send(t("autorole.remove.removed", ctx.language))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return
        guild = member.guild
        if not guild.me.guild_permissions.manage_roles:
            return
        role = await self.bot.get_guild_property(guild, "autorole")
        if not role:
            return
        role = guild.get_role(int(role))
        if role and role < guild.me.top_role:
            await member.add_roles(
                role,
                reason=t("autorole.reason", await self.bot.get_language(guild)),
            )


def setup(bot):
    bot.add_cog(AutoRole(bot))
