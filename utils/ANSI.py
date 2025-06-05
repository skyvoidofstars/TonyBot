# SGR color constants
# rene-d 2018

_ESCAPE_PREFIX: str = '\033'
# _ESCAPE_PREFIX: str = '\u001b'


class Colors:
    LIGHT_BLACK: str = f'{_ESCAPE_PREFIX}[0;30m'
    LIGHT_RED: str = f'{_ESCAPE_PREFIX}[0;31m'
    LIGHT_GREEN: str = f'{_ESCAPE_PREFIX}[0;32m'
    LIGHT_BROWN: str = f'{_ESCAPE_PREFIX}[0;33m'
    LIGHT_BLUE: str = f'{_ESCAPE_PREFIX}[0;34m'
    LIGHT_PURPLE: str = f'{_ESCAPE_PREFIX}[0;35m'
    LIGHT_CYAN: str = f'{_ESCAPE_PREFIX}[0;36m'
    GRAY: str = f'{_ESCAPE_PREFIX}[0;37m'
    DARK_GRAY: str = f'{_ESCAPE_PREFIX}[1;30m'
    RED: str = f'{_ESCAPE_PREFIX}[1;31m'
    GREEN: str = f'{_ESCAPE_PREFIX}[1;32m'
    YELLOW: str = f'{_ESCAPE_PREFIX}[1;33m'
    BLUE: str = f'{_ESCAPE_PREFIX}[1;34m'
    PURPLE: str = f'{_ESCAPE_PREFIX}[1;35m'
    CYAN: str = f'{_ESCAPE_PREFIX}[1;36m'
    WHITE: str = f'{_ESCAPE_PREFIX}[1;37m'
    BOLD: str = f'{_ESCAPE_PREFIX}[1m'
    UNDERLINE: str = f'{_ESCAPE_PREFIX}[4m'
    END: str = f'{_ESCAPE_PREFIX}[0m'


if __name__ == '__main__':
    for i in dir(Colors):
        if i[0:1] != '_' and i != 'END':
            print('{:>16} {}'.format(i, getattr(Colors, i) + i + Colors.END))
