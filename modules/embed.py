from discord import Embed as BaseEmbed, Color


class Embed(BaseEmbed):
    """
    Embed that sends itself as text if there are no embed perms
    """

    def __init__(self, ctx, **kwargs):
        self.ctx = ctx
        super().__init__(**kwargs)
        if not self.color:
            self.color = ctx.me.color if ctx.me.color.value else Color.dark_theme()

    async def send(self, dest=None):
        dest = dest or self.ctx
        channel = getattr(dest, "channel", dest)
        if channel.permissions_for(self.ctx.me).embed_links:
            return await dest.send(embed=self)
        else:
            return await dest.send(self)

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
