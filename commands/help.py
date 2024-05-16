from typing import Mapping

from discord.ext import commands, pages
from discord.ext.commands import Cog, Command, Group

from modules import embed
from modules.i18n import t
from modules.utils import chunks


class Help(commands.DefaultHelpCommand):
    def __init__(self):
        super().__init__(
            verify_checks=False,
            command_attrs={
                "help": "help_command.help",
                "usage": "help_command.usage",
                "checks": [commands.bot_has_permissions(embed_links=True).predicate],
            },
        )

    def command_not_found(self, name: str) -> str:
        return t("help_command.command_not_found", self.context.language, name=name)

    def subcommand_not_found(self, command: Command, name: str) -> str:
        return t(
            "help_command.subcommand_not_found",
            self.context.language,
            command=command.qualified_name,
            subcommand=name,
        )

    async def send_bot_help(self, mapping: Mapping[Cog | None, list[Command]]):
        command_list = await self.filter_commands(sum(mapping.values(), []), sort=True)
        help_pages = []
        for ch in chunks(command_list, 10):
            em = embed.Embed(
                self.context,
                title=t("help_command.command_list", self.context.language),
            )
            for command in ch:
                short_doc = (
                    command.brief or command.help or "help_command.no_description"
                )
                em.add_field(
                    name=command.name,
                    value=t(short_doc, self.context.language).partition("\n")[0],
                    inline=False,
                )
            help_pages.append(em)
        await pages.Paginator(pages=help_pages).send(
            self.context, self.get_destination()
        )

    async def send_group_help(self, group: Group):
        em = self.get_command_embed(group)
        for subcommand in group.commands:
            help_ = t(subcommand.help, self.context.language) if subcommand.help else ""
            em.add_field(
                name=t(
                    "help_command.subcommand",
                    self.context.language,
                    name=subcommand.name,
                ),
                value=self.get_command_signature(subcommand) + "\n" + help_,
                inline=False,
            )
        await em.send(self.get_destination())

    async def send_cog_help(self, cog: Cog):
        await self.get_destination().send(self.command_not_found(cog.qualified_name))

    async def send_command_help(self, command: Command):
        await self.get_command_embed(command).send(self.get_destination())

    def get_command_embed(self, command: Command):
        em = embed.Embed(
            self.context,
            title=command.qualified_name,
            description=t("help_command.help_description", self.context.language),
        )
        em.add_field(
            name=t("help_command.command_usage", self.context.language),
            value=self.get_command_signature(command),
            inline=False,
        )
        if command.help:
            em.add_field(
                name=t("help_command.command_description", self.context.language),
                value=t(
                    command.help,
                    self.context.language,
                    prefix=self.context.clean_prefix,
                ),
                inline=False,
            )
        return em

    def get_command_signature(self, command: Command):
        signature = super().get_command_signature(command)
        return self.r_replace(
            signature,
            command.signature,
            t(command.signature, self.context.language),
            1,
        )

    @staticmethod
    def r_replace(string: str, old: str, new: str, count=-1) -> str:
        return string[::-1].replace(old[::-1], new[::-1], count)[::-1]


def setup(bot):
    bot.help_command = Help()
