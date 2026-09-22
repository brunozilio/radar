"""Package only the public inputs and code required by the existing models."""
import ast
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'projection-runtime'


def build():
    DEST.mkdir(exist_ok=True)
    selected = set()

    def script(name):
        path = ROOT / 'scripts' / name
        if path in selected or not path.exists():
            return
        selected.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ''] if isinstance(node, ast.ImportFrom) else []
            for module in modules:
                if module.startswith('hydro_'):
                    script(module + '.py')

    script('hydro_site_projection.py')
    selected.add(ROOT / 'scripts/hydro-hourly-requirements.txt')
    patterns = {
        'model-artifacts/forecast-6h-v1': ['*.joblib', 'model.json'],
        'model-artifacts/encantado-6h-v1': ['*.joblib', 'model.json'],
        'model-artifacts/santa-tereza-6h-v1': ['*.joblib', 'model.json'],
        'outputs/mucum-propagacao-2026-09-21': ['telemetria.npz', 'chuva-pesos.json', 'grafo-drenagem.json', 'estacoes-conectividade.csv', 'raw/normalized-*.npz', 'raw/chuva-prevista-query.json', 'raw/chuva-previsao-historica-*.json'],
        'outputs/mucum-atualizacao-15h-2026-09-21': ['previsao-atualizada.csv', 'previsao-vazoes-montante.csv', 'roteamento-vazao-pesos.csv', 'conferencia-balanco.json', 'nwp-historical-icon.json', 'raw/ana-*-fresh.xml', 'raw/sigma-*.txt'],
        'outputs/mucum-bacia-2026-09-21': ['raw/upstream-basins.geojson', 'producao-estacoes.json'],
    }
    for directory, globs in patterns.items():
        for pattern in globs:
            found = list((ROOT / directory).glob(pattern))
            if not found:
                raise ValueError(f'Missing runtime input: {directory}/{pattern}')
            selected.update(found)
    manifest = {}
    for source in sorted(selected):
        relative = source.relative_to(ROOT)
        target = DEST / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        manifest[str(relative)] = hashlib.sha256(target.read_bytes()).hexdigest()
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # This directory is generated exclusively by this packager. Never ship
    # diagnostic runs, bytecode or old files from a previous package.
    keep = set(manifest) | {'manifest.json'}
    for path in DEST.rglob('*'):
        if path.is_file() and str(path.relative_to(DEST)) not in keep:
            path.unlink()
    print(f'{len(selected)} runtime files, {sum(p.stat().st_size for p in selected) / 1024**2:.1f} MiB')


if __name__ == '__main__':
    build()
