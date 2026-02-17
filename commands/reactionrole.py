import logging as log

import discord
from discord import Message, PartialEmoji, RawReactionActionEvent
from discord.ext import commands, pages
from sqlalchemy import Column, String

from modules import regexps, embed
from modules.i18n import t
from modules.db import WrappedTable
from modules.utils import chunks
from modules.converters import ReactionConverter, ManageableRole, SameGuildMessage
from modules.prima import (
    HTTP_INVALID_FORM_BODY,
    HTTP_UNKNOWN_EMOJI,
    ADD_ALIASES,
    REMOVE_ALIASES,
)

rr_table = WrappedTable(
    "reaction_roles",
    None,
    Column("guild_id", String(25), nullable=False),
    Column("channel_id", String(25), nullable=False),
    Column("message_id", String(25), nullable=False),
    Column("reaction", String(25), nullable=False),
    Column("role_id", String(25), nullable=False),
)


class ReactionRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = rr_table
        self.data.engine = bot.sql

    @staticmethod
    def get_raw(emoji: PartialEmoji | str) -> str:
        emoji = str(emoji)
        ids = regexps.ID.findall(emoji)
        return ids[-1] if ids else emoji

    @commands.group(aliases=("reaction_role", "rr"), invoke_without_command=True)
    @commands.guild_only()
    async def reactionrole(self, ctx):
        "reactionrole.help"
        await ctx.send_help(ctx.command)

    @reactionrole.command(usage="reactionrole.add.usage", aliases=ADD_ALIASES)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def add(
        self,
        ctx,
        message: SameGuildMessage,
        reaction: ReactionConverter,
        role: ManageableRole,
    ):
        "reactionrole.add.help"
        raw_reaction = self.get_raw(reaction)
        if any(
            r == raw_reaction
            for r, in await self.data.select("reaction", message_id=str(message.id))
        ):
            return await ctx.send(t("reactionrole.add.already_taken", ctx.language))
        try:
            await message.add_reaction(reaction)
        except discord.Forbidden:
            return await ctx.send(
                t("reactionrole.add.missing_reaction_perms", ctx.language)
            )
        except discord.HTTPException as e:
            if e.code == HTTP_INVALID_FORM_BODY:
                e.code = HTTP_UNKNOWN_EMOJI
            raise
        await self.data.insert(
            guild_id=str(ctx.guild.id),
            channel_id=str(message.channel.id),
            message_id=str(message.id),
            reaction=raw_reaction,
            role_id=str(role.id),
        )
        em = embed.Embed(ctx)
        em.add_field(
            name=t("reactionrole.add.added", ctx.language),
            value=t(
                "reactionrole.add.comment",
                ctx.language,
                reaction=reaction,
                url=message.jump_url,
                role=role.mention,
            ),
        )
        await em.send()

    @reactionrole.command()
    async def list(self, ctx):
        "reactionrole.list.help"
        list_pages = []
        for ch in chunks(
            await self.data.select(
                "channel_id",
                "message_id",
                "reaction",
                "role_id",
                guild_id=str(ctx.guild.id),
            ),
            10,
        ):
            records = []
            for channel_id, message_id, reaction, role_id in ch:
                if reaction.isdecimal():
                    reaction = ctx.bot.get_emoji(int(reaction)) or reaction
                records.append(
                    t(
                        "reactionrole.list.item",
                        ctx.language,
                        url="https://discord.com/channels"
                        f"/{ctx.guild.id}/{channel_id}/{message_id}",
                        reaction=reaction,
                        role=f"<@&{role_id}>",
                    )
                )
            list_pages.append(
                embed.Embed(
                    ctx,
                    title=t("reactionrole.list.title", ctx.language),
                    description="\n".join(records),
                )
            )
        if list_pages:
            await pages.Paginator(list_pages).send(ctx)
        else:
            await embed.Embed(
                ctx, title=t("reactionrole.list.empty", ctx.language)
            ).send()

    @reactionrole.command(usage="reactionrole.remove.usage", aliases=REMOVE_ALIASES)
    @commands.has_permissions(manage_guild=True, manage_roles=True)
    async def remove(
        self, ctx, message: SameGuildMessage | int, reaction: ReactionConverter
    ):
        "reactionrole.remove.help"
        message_id = message.id if isinstance(message, Message) else message
        raw_reaction = self.get_raw(reaction)
        for reaction, role_id in await self.data.select(
            "reaction", "role_id", message_id=str(message_id)
        ):
            if reaction == raw_reaction:
                # converter will raise an error on failure
                await ManageableRole().convert(ctx, role_id)
                await self.data.delete(message_id=str(message_id), reaction=raw_reaction)
                await ctx.send(t("reactionrole.remove.removed", ctx.language))
                return
        await ctx.send(t("reactionrole.remove.not_found", ctx.language))

    async def handle_reaction(self, payload: RawReactionActionEvent, method_name: str):
        raw_emoji = self.get_raw(payload.emoji)
        for reaction, role_id in await self.data.select(
            "reaction", "role_id", message_id=str(payload.message_id)
        ):
            if reaction == raw_emoji:
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                role = guild.get_role(int(role_id))
                if member and not member.bot and role and role < guild.me.top_role:
                    await getattr(member, method_name)(
                        role,
                        reason=t(
                            "reactionrole.reason",
                            await self.bot.get_language(guild),
                        ),
                    )
                return

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        await self.handle_reaction(payload, "add_roles")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        await self.handle_reaction(payload, "remove_roles")

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.test_mode:
            log.info("Removing non-working roles for reactions...")
            await self.clean_removed()
            log.info("Completed.")

    async def clean_removed(self):
        for guild in self.bot.guilds:
            checked_messages = set()
            for c, m, r in await self.data.select(
                "channel_id", "message_id", "role_id", guild_id=str(guild.id)
            ):
                channel = self.bot.get_channel(int(c))
                if not channel:
                    await self.data.delete(channel_id=c)
                    continue
                if m not in checked_messages:
                    checked_messages.add(m)
                    try:
                        await channel.fetch_message(int(m))
                    except discord.NotFound:
                        await self.data.delete(message_id=m)
                        continue
                    except Exception:
                        pass
                if not guild.get_role(int(r)):
                    await self.data.delete(role_id=r)


def setup(bot):
    bot.add_cog(ReactionRole(bot))
