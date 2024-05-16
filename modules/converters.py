from discord import Emoji, User, Member, Message, NotFound, Role
from discord.utils import get
from discord.ext.commands import (
    Context,
    BadArgument,
    MemberConverter,
    UserConverter,
    UserNotFound,
    EmojiConverter,
    EmojiNotFound,
    RoleConverter,
    MessageConverter,
)
from modules.regexps import ID


class SmartUserConverter(MemberConverter):
    async def convert(self, ctx: Context, argument: str) -> User | Member:
        if match := ID.search(argument):
            user_id = int(match.group())
            if ctx.guild and (user := ctx.guild.get_member(user_id)):
                return user
            if ctx.message and (user := get(ctx.message.mentions, id=user_id)):
                return user
            if ctx.guild:
                user = await self.query_member_by_id(ctx.bot, ctx.guild, user_id)
            else:
                user = ctx.bot.get_user(user_id)
            if user:
                return user
            try:
                return await ctx.bot.fetch_user(user_id)
            except NotFound:
                raise UserNotFound(argument)
        elif ctx.guild:
            if user := ctx.guild.get_member_named(argument):
                return user
            if user := await self.query_member_named(ctx.guild, argument):
                return user

            arg = argument.casefold()
            user = None
            contains = None
            nick_contains = None

            for member in ctx.guild.members:
                name = str(member).casefold()
                if name.startswith(arg):
                    user = member
                    break
                if contains is None and arg in name:
                    contains = member
                if nick_contains is None and member.nick:
                    if arg in member.nick.casefold():
                        nick_contains = member

            if user := user or contains or nick_contains:
                return user
            else:
                raise UserNotFound(argument)
        else:
            return await UserConverter().convert(ctx, argument)


class SmartEmojiConverter(EmojiConverter):
    async def convert(self, ctx: Context, argument: str) -> Emoji:
        try:
            return await super().convert(ctx, argument)
        except EmojiNotFound:
            # additional name lookup in case name was confused with id
            if ctx.guild and (emoji := get(ctx.guild.emojis, name=argument)):
                return emoji
            if emoji := get(ctx.bot.emojis, name=argument):
                return emoji
            raise


class ReactionConverter(SmartEmojiConverter):
    async def convert(self, ctx: Context, argument: str) -> Emoji | str:
        try:
            return await super().convert(ctx, argument)
        except EmojiNotFound:
            pass
        if argument.isdecimal():
            return f"<:{argument}:{argument}>"
        return argument


class RoleTooHighForUser(BadArgument):
    pass


class RoleTooHighForBot(BadArgument):
    pass


class ManageableRole(RoleConverter):
    async def convert(self, ctx: Context, argument: str) -> Role:
        role = await super().convert(ctx, argument)
        if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            raise RoleTooHighForUser()
        if role >= ctx.me.top_role:
            raise RoleTooHighForBot()
        return role


class NotSameGuild(BadArgument):
    pass


class SameGuildMessage(MessageConverter):
    async def convert(self, ctx: Context, argument: str) -> Message:
        message = await super().convert(ctx, argument)
        if message.guild != ctx.guild:
            raise NotSameGuild()
        return message
