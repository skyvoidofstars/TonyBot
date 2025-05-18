# Config.py structure
```python
from datetime import timedelta, timezone

# Bot prefix
command_prefix = '?'

# Timezone
brasilia_tz = timezone(timedelta(hours=-3))

# Default embeds width
embed_width = 54

# Roles id to use managment commands
AllowedRoles = [
    0000000000000000000  # Role name
]

# Allowed chest slash command channels 
ChestAllowedChannels = [
    0000000000000000000 # Channel name
]

# Discord server id and channel id for bot logs
LogGuild, LogChannel = 000000000000000000, 000000000000000000

# ID to be mentioned in errors or initializations
# 000000000000000000 to user or '&000000000000000000' to roles
MentionID = 000000000000000000
```