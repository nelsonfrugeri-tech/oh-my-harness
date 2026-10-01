import dataclasses
from contextlib import nullcontext
import json
from decimal import Decimal
from enum import Enum

from kb.arguments import parser
from kb.dispatch import dispatch
from kb.runtime import build_context


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        context = build_context(args)
        from kb.adapters.locking import BundleLock
        mutation = args.command in {'write', 'approve', 'move', 'reject', 'repair', 'backup'}
        with BundleLock(context.store.root) if mutation else nullcontext():
            result = dispatch(args, context)
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
    if status in {'Degraded', 'LegacyPending', 'Unavailable'}:
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
