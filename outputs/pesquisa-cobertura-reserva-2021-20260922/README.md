# Cobertura ANA — reserva de maio de 2021

Escopo: Muçum 86510000 e Linha José Júlio 86472000, 28/04–31/05/2021. Aquecimento 28–30/04. Nenhum treino, inferência, cálculo de erros ou seleção de modelo. A reserva continua excluída do ajuste.

Busca restrita em 63 XMLs não encontrou resposta pertinente. Quatro GETs, sem retry automático; status: {'parsed': 4}. Plano registrado antes da rede.

| Posto | Registros | Nível aprovado | Suspeito | Nível vazio | Maio: nível aprovado exato 15min | Maio: nível aprovado exato hora |
|---|---:|---:|---:|---:|---:|---:|
| 86510000 | 3264 | 3264 | 0 | 0 | 2976/2976 | 744/744 |
| 86472000 | 3264 | 0 | 0 | 3264 | 0/2976 | 0/744 |

Duplicatas extras: 0; conflitos: 0. `coverage.json` preserva histogramas de cadência/minuto/segundo, todos os campos/QC, grades exatas e intervalos ausentes ou não aprovados. `daily-coverage.csv` detalha os dias. JSONL mantém todos os campos literais, fonte/hash e índice de registro XML (1-based). XMLs permanecem integrais e imutáveis.

Não arredondamos timestamps nem interpolamos registros; ausência permanece ausência. Unidades/texto numérico permanecem como no XML, sem conversão. Esta auditoria não certifica fuso, datum, vigência da régua, disponibilidade histórica em tempo real nem independência física da vazão reportada. Não foram calculados picos ou métricas de modelos.

Muçum também tem 3.264 vazões finais aprovadas; ChuvaFinal tem 3.256 valores aprovados e oito vazios. Linha tem VazaoFinal vazio nos 3.264 registros; ChuvaFinal tem 3.098 valores aprovados e 166 vazios. Há um NivelDisplay numérico em Linha, sem QC; ele permanece como campo distinto e não substitui NivelFinal. Em ambas as estações, todos os 3.263 intervalos consecutivos têm 900 segundos; não há registros fora da grade nem lacunas de timestamps. As lacunas descritas são de campos/QC.
