"""Durable local outbox for immutable forecast evidence (including blocked attempts)."""
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
from pathlib import Path


def digest(body):
    return hashlib.sha256(body).hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                       separators=(',', ':')) + '\n').encode()


def atomic(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(path.name + '.pending')
    pending.write_bytes(body)
    os.replace(pending, path)


def bundle(root, files):
    """Stable bytes: content-addressed runtimes are shared by all their receipts."""
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as tar:
            for relative in sorted(set(files)):
                relative = Path(relative)
                if relative.is_absolute() or '..' in relative.parts:
                    raise ValueError('Archive path escapes root')
                path = root / relative
                if not path.resolve().is_relative_to(root.resolve()) or any((root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)):
                    raise ValueError('Archive symlink or path escapes root')
                if not path.is_file() or path.is_symlink():
                    raise ValueError(f'Archive input must be a regular file: {relative}')
                body = path.read_bytes()
                info = tarfile.TarInfo(str(relative))
                info.size = len(body)
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(body))
    return stream.getvalue()


def runtime_bundle(root):
    manifest = root / 'manifest.json'
    if manifest.exists():
        specification = json.loads(manifest.read_text())
        for name, expected in specification.items():
            if Path(name).is_absolute() or '..' in Path(name).parts or digest((root / name).read_bytes()) != expected:
                raise ValueError(f'Runtime manifest integrity failure: {name}')
        return bundle(root, [*specification, 'manifest.json'])
    # Direct local execution also preserves code and frozen weights. Packaged
    # production includes the full verified manifest and seed inputs above.
    files = [p.relative_to(root) for p in (root / 'scripts').glob('hydro_*.py')]
    files += [Path('scripts/hydro-hourly-requirements.txt')]
    for name in ('forecast-6h-v1', 'encantado-6h-v1', 'santa-tereza-6h-v1', 'mucum-propagation-v1'):
        files += [p.relative_to(root) for p in (root / 'model-artifacts' / name).glob('*') if p.is_file()]
    return bundle(root, files)


def enqueue_attempt(state, out, root, *, attempt_id, reference_at, status,
                    generated_at=None, missing=None, error=None):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', attempt_id):
        raise ValueError('Invalid archive attempt identifier')
    archive = state / 'archive'
    objects = []
    def add(body, role):
        sha = digest(body)
        key = f'projection/blobs/{sha}.tar.gz'
        target = archive / 'blobs' / f'{sha}.tar.gz'
        if target.exists() and digest(target.read_bytes()) != sha:
            raise ValueError('Existing archive blob is corrupt')
        if not target.exists():
            atomic(target, body)
        objects.append(dict(key=key, sha256=sha, bytes=len(body), role=role))
    add(runtime_bundle(root), 'runtime')
    names = ['collection-manifest.json', 'input-readiness.json', 'reference-selection.json', 'model-metadata.json',
             'feature-snapshot.json', 'short-term-shadow.json', 'propagation-shadow.json',
             'local-nowcast-shadow.json', 'rain-context-shadow.json', 'forecast.json']
    files = [Path(name) for name in names if (out / name).is_file()]
    files += [p.relative_to(out) for p in (out / 'raw').rglob('*') if p.is_file()]
    add(bundle(out, files), 'attempt')
    receipt = dict(schema='radar-archive-receipt/v1', attemptId=attempt_id,
                   referenceAt=reference_at, status=status, generatedAt=generated_at,
                   missing=missing or [], error=error, objects=objects,
                   retention='No automatic time-based expiration',
                   datum='ANA station reference; absolute datum not independently verified')
    body = canonical(receipt)
    target = archive / 'pending' / f'{attempt_id}.json'
    if target.exists() and target.read_bytes() != body:
        raise ValueError('Attempt evidence cannot be overwritten')
    atomic(target, body)
    return f'projection/receipts/{attempt_id}.json'
