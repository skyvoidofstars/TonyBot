from datetime import timedelta, timezone

# Prefixo para os comandos do bot
command_prefix = '?'

# Define a timezone para Brasília (UTC-3)
brasilia_tz = timezone(timedelta(hours=-3))

# Define a largura em caracteres para embeds
embed_width = 54

# Lista de cargos permitidos para certos comandos
AllowedRoles = [
    925570115167203338,  # Cargo de Diretor
    925570190702428171,  # Cargo de Gerente
    925570160390201375,  # Cargo de Supervisor (a)
    1024067238711525436, # Cargo de Dev Bot
    1364946499712061514, # Cargo de Testes (Servidor de Testes)
]

# Lista dos canais onde o baú pode ser usado
ChestAllowedChannels = [
    1144661772482134128, # canal de testes
    1365147589963415562, # Canal de baú da Los Santos Custom
]

# Servidor e canal para logs
LogGuild, LogChannel = 798279120638574652, 1144661772482134128