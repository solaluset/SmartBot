from functools import partial

from discord import Embed as BaseEmbed, Color


class Embed(BaseEmbed):
    """
    Embed that sends itself as text if there are no embed perms
    """

    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        super().__init__(**kwargs)
        if not self.color:
            self.color = (
                ctx.me.color if ctx.me and ctx.me.color.value else Color.dark_theme()
            )

    async def send(
        self, dest=None, *, content: str | None = None, ephemeral: bool = False
    ):
        dest = dest or self.ctx
        channel = getattr(dest, "channel", dest)
        if hasattr(dest, "respond"):
            method = partial(dest.respond, ephemeral=ephemeral)
        else:
            if ephemeral:
                raise TypeError(f"{dest} does not support ephemeral messages")
            method = dest.send
        if (
            not hasattr(channel, "permissions_for")
            or channel.permissions_for(self.ctx.me).embed_links
        ):
            return await method(content, embed=self)
        else:
            if content:
                content = f"{content}\n{self}"
            else:
                content = self
            return await method(content)

    def __str__(self) -> str:
        text = ""
        if self.author:
            text += self.author.name + "\n"
        if self.url and self.title:
            title = f"[{self.title}]({self.url})"
        else:
            title = self.title
        if title:
            text += f"**{title}**\n"
        if self.description:
            text += self.description + "\n"
        for field in self.fields:
            text += f"**{field.name}**\n{field.value}\n"
        if self.image:
            text += self.image.url + "\n"
        if self.timestamp:
            timestamp = f"<t:{int(self.timestamp.timestamp())}:f>"
        else:
            timestamp = None
        if self.footer:
            footer = self.footer.text
        else:
            footer = None
        return text + " • ".join(filter(None, (footer, timestamp)))
