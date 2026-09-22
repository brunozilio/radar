"""Verify the completed fixed Radar comparison, then write a descriptive report."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from hydro_hourly_forecast import epoch, iso
from hydro_radar_native_missing import training_masks
from hydro_routing_fit import shift

OUT = Path(__file__).resolve().parent
RUN = ROOT/'outputs/experimento-radar-ausencias-reservatorios-20260921'
NATIVE = ROOT/'outputs/experimento-radar-ausencias-nativas-runtime19-20260921'
LEVELS = ROOT/'outputs/experimento-radar-niveis-reservatorios-20260921'


def read(path):
    return list(csv.DictReader(path.open()))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    manifest = json.loads((RUN/'artifact-hashes.json').read_text())
    for r in manifest:
        assert digest(RUN/r['file']) == r['sha256']
    exp = json.loads((RUN/'experiment.json').read_text())
    for path,value in exp['input_sha256'].items():
        assert digest(Path(path)) == value
    rows = read(RUN/'predictions.csv')
    data = dict(np.load(LEVELS/'features.npz'))
    times,F,base,truth,complete = (data[k] for k in ('times','features','base','truth','complete24'))
    positions = {iso(t):i for i,t in enumerate(times)}
    info = {(r['phase'],int(r['horizon_h'])):r for r in read(RUN/'training.csv')}
    checks = []
    for phase in ('validation','test'):
        for h in range(1,13):
            group = [r for r in rows if r['phase']==phase and int(r['nominal_lead_h'])==h]
            selected = [r for r in group if r['combined_m']]
            ix = np.array([positions[r['origin']] for r in selected])
            model = joblib.load(RUN/'models'/f'{phase}-{h}.joblib')
            expected = np.array([float(r['combined_m']) for r in selected])
            actual = model.predict(F[ix])+base[ix]
            np.testing.assert_array_equal(actual,expected)
            target = shift(truth,-h)
            mask = training_masks(times,base,target,complete,h,epoch('2025-10-01T00:00:00-03:00'),epoch('2026-07-01T00:00:00-03:00'))[phase,'candidate']
            meta = info[phase,h]
            assert mask.sum() == int(meta['n'])
            assert ((~complete)&mask).sum() == int(meta['with_missing_first24'])
            assert ((~np.isfinite(F[:,180:]).all(axis=1))&mask).sum() == int(meta['with_missing_reservoirs'])
            assert ((target>=7)&mask).sum() == int(meta['targets_ge_7m'])
            assert np.all(times[mask]+h*3600<epoch(meta['cutoff_exclusive']))
            assert model.n_features_in_ == 204 and model.n_iter_ == 180
            assert model.get_params()['max_leaf_nodes'] == int(meta['leaf_nodes'])
            assert model.get_params()['loss'] == meta['loss']
            assert all(p[0].nodes[0]['count']==int(meta['n']) for p in model._predictors)
            checks.append(dict(phase=phase,horizon_h=h,rows=len(group),predictions=len(selected),max_reproduction_difference_m=float(abs(actual-expected).max())))
    metrics = read(RUN/'evaluation.csv')
    def key(r):
        return r['phase'],r['horizon_h'],r['subset'],r['population'],r['family']
    current = {key(r):r for r in metrics}
    control_metric_checks = 0
    for folder, mapping in [(NATIVE,{'baseline':'baseline','candidate':'native_only'}),(LEVELS,{'candidate':'reservoir_only'})]:
        for r in read(folder/'evaluation.csv'):
            if r['family'] not in mapping:
                continue
            translated = dict(r,family=mapping[r['family']])
            assert current[key(translated)] == translated
            control_metric_checks += 1
    live = np.array([float(r['value']) for r in read(ROOT/'outputs/auditoria-compatibilidade-ceran-radar-20260921/live-features.csv')])
    domain = []
    for phase in ('validation','test'):
        for h in range(1,13):
            target = shift(truth,-h)
            mask = training_masks(times,base,target,complete,h,epoch('2025-10-01T00:00:00-03:00'),epoch('2026-07-01T00:00:00-03:00'))[phase,'candidate']
            added = F[mask,180:]
            domain.append(dict(phase=phase,horizon_h=h,outside_expanded_train=int(((live<np.nanmin(added,axis=0))|(live>np.nanmax(added,axis=0))).sum())))
    summary = dict(models_verified=len(checks),maximum_reproduction_error_m=max(r['max_reproduction_difference_m'] for r in checks),
                   control_metric_rows_exact=control_metric_checks,input_hashes_verified=len(exp['input_sha256']),
                   artifact_hashes_verified=len(manifest),checks=checks,domain=domain,
                   promoted=False,prospective=False,goal_achieved=False)
    (OUT/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines = ['# Radar: treino com faltas e níveis de reservatórios','',
             'Comparação histórica de desenvolvimento. Quatro versões nas mesmas102.084 origens/horizontes: referência, treino com faltas, níveis adicionais e combinação dos dois. Controles congelados;24 modelos combinados novos. Sem busca de parâmetros, seleção de horizontes, promoção ou emissão ao vivo.','',
             'Acerto: erro absoluto ≤0,50 m. Cheia: nível observado ≥7 m, recorte analítico. Os nomes validation/test são cortes históricos já inspecionados, não validação independente.','',
             '**Resultado misto, sem promoção.** Na cheia de test, a combinação reduz o MAE em 6h, mas perde acertos em alguns horizontes. Em 12h, seu maior erro supera a referência e a versão com níveis adicionais. Também há perdas na fase validation. Não escolher versões por horizonte usando estes resultados já vistos. changes.csv preserva as diferenças contra as três versões em todos os horizontes.','',
             '| Fase | Horizonte | Versão | Acertos na cheia | MAE cheia (m) | Maior erro cheia (m) |',
             '|---|---:|---|---:|---:|---:|']
    labels = {'baseline':'Referência','native_only':'Treino com faltas','reservoir_only':'Níveis adicionais','combined':'Combinação'}
    for phase in ('validation','test'):
        for h in (1,6,12):
            for family in labels:
                r = current[phase,str(h),'level_ge_7m','full_schedule',family]
                lines.append(f"| {phase} | {h}h | {labels[family]} | {r['hits']}/{r['n']} ({100*float(r['hit_fraction']):.2f}%) | {float(r['mae_m']):.4f} | {float(r['max_abs_m']):.4f} |")
    lines += ['', '## Cobertura e limitações', '',
              'Na cheia da fase test, cada horizonte tem237 alvos observados:236 pares e uma falha por ausência do nível-base, igual nas quatro versões. Os percentuais da tabela usam os236 pares. Em1h,230 acertos são97,46% dos pares e97,05% dos alvos incluindo a falha. A revisão independente do agente confirmou os24 resultados de cheia da combinação, sem dominância sobre as três versões anteriores.', '',
              'Todos os modelos mantêm a mesma disponibilidade de previsão. Linhas sem alvo continuam no arquivo; somente falta do nível-base impede previsão. evaluation.csv preserva todos os12 horizontes, os recortes geral/cheia e entradas completas/com faltas, com cobertura e falhas.', '',
              'O treino ampliado tem7 linhas com ausência nos níveis novos em1h e6 em6h/12h, concentradas em30/05/2025 e com alvos abaixo7m. Isso não comprova robustez a falhas durante cheias.', '',
              'Os campos do vetor das21h fora das faixas de treino caem de17 para11 na fase test (18 para12 na validation). Três campos agora parecem cobertos porque entra o pico suspeito de168,74m no jusante de Julho e suas inclinações. A contagem menor não comprova melhor cobertura física; o dado foi preservado sem correção nesta rodada.', '',
              f"Verificação: inferência dos24 modelos reproduzida exatamente;{control_metric_checks} linhas de métricas dos controles coincidem integralmente com as rodadas anteriores. Memberships, cortes, contagens, parâmetros e hashes conferidos. Cinco testes focados de ausência/corte/seleção temporal passaram antes da avaliação.", '',
              'Os resultados não demonstram98% prospectivos. Persistem hipóteses de disponibilidade, fonte revisada, fuso/datum não certificados e diferenças entre chuva histórica e previsão ao vivo. Nenhuma alteração da automação ou do modelo operacional.']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    (OUT/'artifact-hashes.json').write_text(json.dumps([dict(file=str(p.relative_to(OUT)),sha256=digest(p)) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='artifact-hashes.json'],indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('checks','domain')},indent=2))
    print('\n'.join(lines[7:32]))


if __name__=='__main__':
    with threadpool_limits(limits=2): run()
