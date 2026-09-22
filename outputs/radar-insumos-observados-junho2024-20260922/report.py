from pathlib import Path
import json
P=Path(__file__).resolve().parent
c=json.loads((P/'coverage.json').read_text());v=json.loads((P/'verification.json').read_text())
empty=[r['station'] for r in c if not r['output_records']]
text='''# ANA observado — 27 postos, 12–21/06/2024

Acervo completo dentro do escopo de coleta: **27 códigos exatamente do mapa congelado em latencies.json**, com 12–14/06 como aquecimento e 15–21/06 como janela central. Foram feitas **27 consultas novas**, com até duas conexões e uma tentativa por intervalo/código; quatro XMLs e seus recibos centrais foram reutilizados, inclusive a resposta Sem dados de Carreiro. Plano registrado antes da rede. Nenhuma consulta adicional, matriz, modelo, inferência, ONS ou previsão meteorológica.

As 31 respostas retornaram HTTP200: **23 contêm registros e 8 trazem Sem dados**. Nenhuma falha HTTP/rede. São **6.315 registros brutos e 6.315 linhas ALL-QC**, sem duplicatas idênticas para unir ou conflitos de timestamp. Os 27 JSONLs existem, inclusive sete vazios. Ausência no endpoint não comprova ausência em todos os acervos.

## Cobertura e qualidade

Muçum86510000 tem **960 níveis aprovados em grade de15min completa**. Santa Tereza86472600 tem **944 níveis aprovados**: faltam12 slots em13/06 18:00–20:45 e4 slots em14/06 11:00–11:45, todos no aquecimento. A semana central permanece completa. Linha José Júlio86472000 tem960 registros, mas os níveis final/sensor continuam vazios; sua chuva é finita e aprovada. Carreiro86500000 está sem registros nos dois segmentos. O código86472600 foi mantido como Santa Tereza, sem confundi-lo com Santa Lúcia.

Somando postos de diferentes cadências: **5.262 níveis finais finitos/aprovados e5.660 chuvas finais finitas/aprovadas**. Há655 campos ChuvaFinal vazios, nenhuma chuva numérica negativa ou finita comQC não aprovado. Isso não torna as amostras temporalmente equivalentes nem demonstra cobertura regional suficiente.

Casos relevantes para preparar posteriormente os insumos:

- **QC aprovado não torna campo vazio um valor medido.** Em86200900 e86495500, as240 chuvas de cada posto são vazias, apesar doQC aprovado. Em86448000, as173 chuvas e45 níveis são vazios, também sobQC aprovado. Permanecem desconhecidos.
- **86160000:**556 registros de15min, com uma grande lacuna;508 níveis aprovados,47 níveis suspeitos e1 vazio. Há2 chuvas vazias. Todos permanecem preservados.
- **86125000:**82 registros apenas de20/06 07:29 a21/06 23:59, cadência30min literal em:29/:59. Nenhum foi arredondado para hora/quarter-hour; as grades diagnósticas de presença exata não significam perda do registro original.
- **86410800** começa em17/06 09h; **86471000**, em16/06 16h; **86505500** tem somente7 registros em21/06 17–23h. Outros postos como86117000,86280500 e86488000 têm intervalos longos entre registros apesar de moda horária.
- Para chuva integrada, a presença de valor aprovado não dispensa conferir a duração do intervalo. Não foi aplicada nesta coleta qualquer integração, tolerância, redistribuição, ajuste de pesos ou renormalização.

Sete postos inteiramente sem registros: '''+', '.join(empty)+'''. A oitava resposta Sem dados é o segundo segmento de Carreiro. Zero numérico reportado é preservado; campo vazio e resposta sem registros nunca viram zero.

| Posto | Registros | Moda da cadência(s) | Nível finito/aprovado | Chuva finita/aprovada | Chuva vazia |
|---|---:|---:|---:|---:|---:|
'''
for r in c:
 text+=f"|{r['station']}|{r['output_records']}|{r['modal_step_seconds'] if r['modal_step_seconds'] else '—'}|{r['fields']['NivelFinal']['finite_approved']}|{r['fields']['ChuvaFinal']['finite_approved']}|{r['fields']['ChuvaFinal']['empty']}|\n"
text+='''
## Proveniência e arquivos

- `stations/ana-COD-all-qc.jsonl`: todos os campos originais no topo, valores textuais sem conversão, elemento XML vazio como null; campos inexistentes permanecem inexistentes. Registros ordenados por DataHora literal, com `source_file`, `source_sha256`, `source_record_index`1-based e `source_references`.
- `raw/`: corpos integrais,27 arquivos de tentativa antes da rede, recibos comURL/headers/status/horários UTC/hash. Reutilizados são cópias idênticas porhash e preservam recibo/hora de coleta original, distintos da hora da cópia local.
- `source-manifest.json` e `source-status.json`:31 fontes, ordem explícita, reuso e mensagens ErrorTable; HTTP/rede/parse/vazio são separados.
- `coverage.json`, `field-coverage.csv`, `daily-coverage.csv`: cobertura por posto/campo/dia,QC, cadências, lacunas nas grades exatas900/3600s e timestamps fora de grade. Buracos de15min de uma estação horária não são necessariamente falha do fornecedor.
- `conflicts.json`: vazio. A regra mescla somente dicionários originais integralmente idênticos, guardando todas as proveniências. Registros diferentes no mesmo timestamp seriam separados e sinalizados, nunca escolhidos por precedência ou reparados.

`prepare.py` registra o plano; `collect.py` não repete tentativas já registradas e não segue redirecionamentos automaticamente; `audit.py` reconcilia integralmente cada dicionário XML comJSONL e proveniência, identidade, limites dos segmentos, escopo e hashes. Os intervalos warmup/central não se sobrepõem. A ordem do manifesto não autoriza substituir valores: ordenação cronológica e igualdade integral governam a união.

Os horários são literais, sem conversão de fuso/DST, arredondamento ou certificação de publicação histórica. Headers/coleta atuais não provam quando o dado ouQC foi originalmente publicado. Unidades, referência vertical e continuidade da régua não ganharam certificação nesta coleta. Receber dados retrospectivos não prova disponibilidade ao emitir uma previsão naquele momento.

Nenhuma regra de atraso/peso foi alterada; nenhum cache anterior ou arquivo operacional foi modificado. A cobertura não mede precisão e não implica atingir98%. A admissibilidade de matriz/treino depende de etapa e protocolo separados.

'''
text+=f"**Verificação: {v['check_count']} checks passaram; {v['raw_records']} registros XML representados exatamente uma vez; 31 hashes de fontes conferidos ao final.** Manifesto próprio e manifest-check selam esta pasta.\n"
(P/'README.md').write_text(text)
