import dataclasses
from contextlib import nullcontext
import json
from decimal import Decimal
from enum import Enum
import sys

from kb.adapters.paths import InvalidConfig, MissingPath
from kb.arguments import parser
from kb.dispatch import dispatch
from kb.runtime import build_context

# Commands that never open the bundle; resolving its root for them would ask for a path in vain.
STORELESS = frozenset({'template', 'harvest'})
PATH_EXITS = {'MissingPath': 5, 'InvalidPath': 6}


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        context = None if args.command in STORELESS else build_context(args)
        from kb.adapters.locking import BundleLock
        mutation = args.command in {'write', 'approve', 'move', 'reject', 'repair', 'backup'}
        with BundleLock(context.store.root) if mutation else nullcontext():
            result = dispatch(args, context)
    except (MissingPath, InvalidConfig) as error:
        # A path problem needs the user, not a retry: report it apart from Degraded and Rejected.
        print(error, file=sys.stderr)
        status = 'MissingPath' if isinstance(error, MissingPath) else 'InvalidPath'
        result = {'status': status, 'reason': str(error)}
    except (ValueError, TypeError, KeyError) as error:
        result = {'status': 'Rejected', 'errors': [str(error)]}
    except (OSError, RuntimeError, ImportError) as error:
        result = {'status': 'Degraded', 'reason': f'{type(error).__name__}: {error}'}
    if isinstance(result, str) and not args.json:
        print(result)
        return 0
    payload = _payload(result)
    print(json.dumps(payload, ensure_ascii=False, default=_serialize))
    status = payload.get('status') if isinstance(payload, dict) else None
    if status == 'Pending':
        return 3
    if status in PATH_EXITS:
        return PATH_EXITS[status]
    if status in {'Degraded', 'LegacyPending', 'Unavailable', 'Blocked'}:
        return 4
    if status == 'Rejected' or status == 'Checked' and payload.get('errors'):
        return 2
    return 0


def _payload(result):
    if dataclasses.is_dataclass(result):
        return {'status': type(result).__name__, **dataclasses.asdict(result)}
    return result


def _serialize(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if hasattr(value, 'model_dump'):
        return value.model_dump(mode='json')
    raise TypeError(f'Cannot serialize {type(value).__name__}')
