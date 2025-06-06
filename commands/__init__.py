import os, importlib


def load_all_commands(bot):
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = f'{__name__}.{filename[:-3]}'
            module = importlib.import_module(module_name)
            if hasattr(module, 'setup_commands'):
                module.setup_commands(bot)
