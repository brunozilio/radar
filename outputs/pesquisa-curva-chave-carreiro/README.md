# Curva-chave oficial — Passo Carreiro 86500000

Pesquisa delimitada em 21/09/2026. **Não foi obtida curva com vigência e referência de régua verificadas para julho/2026. Os 34 níveis aprovados sem vazão não foram convertidos.**

## Documento oficial encontrado

O [relatório SGB/CPRM de março/2014](https://rigeo.sgb.gov.br/jspui/bitstream/doc/24596/1/sistema%20de%20alerta_taquari_2014.pdf), já preservado no acervo, contém curva de Passo Carreiro. Na página 36 do PDF, tabela 5.7, os três ramos são 45–480, 480–990 e 990–2060 cm; todas as vigências terminam em 31/12/2013. A figura 5.8 compara curvas anteriores/posteriores a junho/2010.

No anexo, página59, a coluna 86500000 traz h0=0,55; n=1,95; a=31,07; c1=100; c2=2060, conferidos visualmente. As páginas seguintes contêm tabela cota/vazão. O conjunto/faixa do anexo não replica os três ramos da tabela 5.7; não resolvemos essa diferença por inferência ou ajuste. h0 é parâmetro da curva, não comprovação do zero altimétrico da régua.

O documento também apresenta a estação como rio Carreiro na tabela cadastral, mas como Guaporé na tabela/figura da curva: inconsistência editorial preservada. O código 86500000 identifica a coluna examinada. Não existe nessa evidência antiga comprovação de continuidade da curva, zero da régua ou seção após as cheias recentes.

## Caminho atual oficial

A [documentação pública ANA HidroWebService](https://www.ana.gov.br/hidrowebservice/swagger-ui/index.html) enumera GET /EstacoesTelemetricas/HidroSerieCurvaDescarga/v1, para curvas de descarga por estação e período, limitado a 366 dias por pedido. O [manual oficial](https://www.gov.br/ana/pt-br/assuntos/monitoramento-e-eventos-criticos/monitoramento-hidrologico/orientacoes-manuais/manuais/manual-hidrowebservice_publica.pdf), já no acervo, exige cadastro/autenticação. Não tentamos autenticar ou usar credenciais. A recuperação direta do Swagger nesta rodada retornou 503; o método foi verificado no conteúdo indexado público.

O [aviso ANA](https://telemetriaws1.ana.gov.br/Mapa.aspx), já consultado no acervo e novamente indexado nesta pesquisa, indica hidro@ana.gov.br como canal de solicitação de acesso à API. Nenhuma mensagem foi enviada. A existência do método não garante que a curva 86500000 para julho/2026 esteja disponível ou que responda com referência vertical suficiente.

## Pista pública que não fecha o contrato

A [página HidroAPP/UFSC da estação](https://www.labhidro.ufsc.br/hidroapp/hidroapp_data/DADOS/86500000/86500000.html) aparece na busca com análise de curva-chave e cotas relativas ao zero da régua. Isso é produto analítico universitário, não declaração do operador de vigência em julho/2026. A captura direta falhou na verificação TLS por incompatibilidade de hostname; a ferramenta web retornou 502. Não desabilitamos a verificação e não tratamos o resultado indexado como tabela oficial recuperada.

## O que falta para admitir uma conversão

1. Curva aprovada do código 86500000 que cubra 23/07/2026, incluindo todos os ramos, unidades, fórmula/tabela, início/fim de vigência e status/revisão.
2. Vínculo explícito com a régua que produziu os 34 níveis 464,8–517,2 cm, inclusive eventuais mudanças de zero, seção ou sensor.
3. Faixa efetivamente medida/calibrada e limites de extrapolação. As cotas atravessam 480 cm, fronteira presente na tabela antiga; não selecionar um ramo antigo por conveniência.
4. Medições e inspeções que sustentem a versão vigente. A coincidência eventual entre valores antigos e atuais não comprova vigência.

Próximo passo concreto: obter esses metadados pelo canal oficial ANA/SGB ou por exportação pública documentada do Hidroweb. Manter as 34 vazões ausentes até existir informação admissível e um protocolo separado para derivação, sem reclassificar estimativas como vazões observadas.

Arquivos: sources.json preserva URLs, falhas e hashes do acervo reutilizado; historical-curve-metadata.json transcreve os números antigos sem aplicá-los; search-log.json registra buscas e limites; a imagem renderizada preserva a conferência visual do anexo. Nenhum script compartilhado, modelo ou dado anterior foi modificado.
