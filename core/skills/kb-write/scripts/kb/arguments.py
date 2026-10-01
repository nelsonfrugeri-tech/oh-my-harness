import argparse


COMMANDS = ('template', 'validate', 'write', 'approve', 'move', 'reject', 'nav',
            'check', 'harvest', 'backup', 'search', 'repair')


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='kb')
    commands = root.add_subparsers(dest='command', required=True)
    for name in COMMANDS:
        command = commands.add_parser(name)
        command.add_argument('--json', action='store_true')
        command.add_argument('--root')
        command.add_argument('--identity')
        command.add_argument('--qdrant-url')
        command.add_argument('--collection')
        if name in {'validate', 'write', 'approve', 'move', 'reject', 'nav', 'repair'}:
            command.add_argument('--path', required=True)
        if name in {'validate', 'write'}:
            command.add_argument('--file', required=True)
            command.add_argument('--approved-degraded', action='store_true')
        if name in {'validate', 'write', 'approve', 'harvest'}:
            command.add_argument('--transcript', required=name == 'harvest')
        if name in {'write', 'repair', 'move'}:
            command.add_argument('--description', action='append', default=[])
        if name == 'write':
            command.add_argument('--reason', default='')
        if name == 'move':
            command.add_argument('--to', required=True)
        if name == 'template':
            command.add_argument('type', choices=('decision', 'event', 'procedure', 'reference', 'conversation'))
        if name == 'backup':
            mode = command.add_mutually_exclusive_group(required=True)
            mode.add_argument('--dry-run', action='store_true')
            mode.add_argument('--apply', action='store_true')
            command.add_argument('--reason', default='Preservação do modelo anterior da knowledge base.')
            command.add_argument('--plan', default='kb-note-model-r1')
        if name == 'search':
            command.add_argument('query')
            command.add_argument('--history', action='store_true')
            command.add_argument('--legacy', action='store_true')
            command.add_argument('--filters', default='{}')
    return root
