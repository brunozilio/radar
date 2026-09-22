# Níveis de montante — 15–21/06/2024

**Santa Tereza tem série completa de nível; Linha José Júlio tem registros sem nível; Passo Carreiro retorna “Sem dados”.** Três consultas públicas ANA, todas HTTP200, sem retentativas. Nenhum treino, matriz ou preenchimento foi executado.

| Estação | Resposta / nível | Cadência e cobertura | Âncoras válidas /168 |
|---|---|---|---:|
| Linha José Júlio86472000 |672 registros; `NivelFinal` e `NivelSensor` nulos, ambos QC vazios em672/672 |Grade de15min completa,15/06 00:00–21/06 23:45; nenhum nível aproveitável |0 |
| Santa Tereza86472600 |672 níveis finais e sensor finitos/aprovados, iguais em672/672 |Grade de15min completa, sem lacunas |167 |
| Passo Carreiro86500000 |HTTP200 com `ErrorTable`: “Sem dados para esta estação (Código: 86500000) no período solicitado!” |Zero registros; cadência não observável |0 |

O nome de86472600 é **Santa Tereza**, conforme identificação na p.2 dos [boletins SGB17/06](https://www.sgb.gov.br/sace/boletins/Taquari/20240617_22-20240617%20-%20231329.pdf) e [20/06](https://www.sgb.gov.br/sace/boletins/Taquari/20240620_07-20240620%20-%20091414.pdf) já preservados. O código solicitado foi mantido; não houve troca para Santa Lúcia. Nenhum acervo anterior foi renomeado.

## Valores, QC e lacunas

Em Santa Tereza, `NivelFinal` e `NivelSensor` variam de152 a1638cm, sem negativos, zeros ou valores não finitos. Máximo **discreto** em17/06/2024 11:00 literal:16,38m; não certificamos pico contínuo. Os dois pontos dos boletins coincidem exatamente com o XML:17/06 22:00=1407cm e20/06 07:00=817cm. Os boletins explicitam cm; o XML não inclui unidade por registro.

`NivelManual` e `NivelDisplay` estão nulos nas duas séries com registros. Não há duplicatas ou conflitos. `summary.json` distingue campo presente mas vazio, valor não finito, QC vazio/aprovado, grade ausente e resposta `Sem dados`. Em Carreiro, contagem de nulos igual a zero significa ausência de registros para contar, não existência de níveis válidos. Os672 horários sem registro nesse retorno são um denominador de consulta esperado, sem afirmar que a estação transmitia nessa cadência.

Linha tem672 timestamps válidos sem nível, portanto a ausência não resulta de descarte ao colocar dados numa grade. Os boletins também a indicam em manutenção; isso corrobora a indisponibilidade publicada naquele contexto, sem identificar data de reinstalação. Em Carreiro, `Sem dados` é resposta de aplicação recebida com sucesso, não falha de rede nem prova de que não exista registro em outro acervo.

## Conferência das âncoras, sem construir matriz

Para168 origens de hora inteira dentro da semana, foi selecionado o registro mais recente até a consultaO−atraso, sem pular o registro mais novo quando o nível é inválido. A idade máxima após a consulta é15min. Atrasos: Linha30min, Santa Tereza15min e Carreiro30min. Somente nível final finito com QC explicitamente aprovado é elegível; sensor nunca substitui valor final ausente/reprovado.

- Linha:167 consultas selecionam registro com nível vazio; a primeira não tem registro anterior dentro da sondagem.
- Santa Tereza:167 âncoras aprovadas, todas exatamente emO−15min; a primeira origem não possui a margem anterior nesta coleta.
- Carreiro:168 consultas sem registro disponível.

Os504 rastros estão em `anchor-source-trace.csv`, com horário de consulta, registro escolhido, idades, índices XML, valores e motivos. Esses atrasos são convenções experimentais; uma série recuperada hoje não certifica a disponibilidade histórica na origem. Nenhuma conversão de fuso, arredondamento ou adaptação de contrato foi aplicada.

## Proveniência e encerramento

Inventário anterior às consultas não encontrou respostas desses postos nessa janela. `plan.json` registra escopo e limites; `collect.py` preserva uma tentativa por posto, incluindo URL, início/fim UTC, status, headers, corpo e SHA256 em `raw/`. Os arquivos `ana-COD-all-qc.jsonl` mantêm **todos os campos originais**, QC e valores vazios, ordenados com índice XML1-based e hash de origem; Carreiro gera JSONL vazio coerente com a resposta. Campos acessórios devolvidos pelo mesmo endpoint foram preservados incidentalmente, sem consultas adicionais de chuva ou usinas e sem usá-los nesta auditoria.

`audit.py` confere integralmente1344 registros XML↔JSONL, hashes dos recibos e pontos dos boletins. Fontes SGB reutilizadas e seus hashes constam de `source-manifest.json`. `verification.json` e `manifest-check.json` passaram. `manifest.json` sela os artefatos.

Não foi localizada aqui nova informação de datum, vigência da régua, fuso ou publicação/revisão. Referência local das réguas não estabelece equivalência entre estações ou períodos. Nenhuma licença específica de redistribuição foi identificada nos corpos; preservação local com atribuição, sem publicação externa. Escopo fechado após3GETs, sem novas buscas, contatos, inferência ou alteração operacional.
