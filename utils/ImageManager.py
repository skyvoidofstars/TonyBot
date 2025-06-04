import discord


def get_image_url_from_message(message: discord.Message) -> str | None:
    if not message.attachments:
        return None

    _urls: list[str] = []

    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            _urls.append(attachment.url)
        elif attachment.height is not None and attachment.width is not None:
            common_image_extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp")
            if attachment.filename.lower().endswith(common_image_extensions):
                _urls.append(attachment.url)
    return _urls
