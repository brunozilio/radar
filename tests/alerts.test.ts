import assert from "node:assert/strict";
import test from "node:test";

import {
  extractDefenseCivilAlertCandidates,
  extractDefenseCivilImage,
  isDefenseCivilAlertRelevant,
  parseDefenseCivilAlerts,
  parseDefenseCivilArticle,
  validUntilFromDefenseCivilCardText,
  validUntilFromDefenseCivilText,
} from "../lib/alerts.ts";

const CURRENT_LISTING_HTML = `
<article class="conteudo-lista__item clearfix">
  <header>
    <time datetime="2026-08-26T12:43:00-0300">26/08/2026</time>
    <h2 class="conteudo-lista__item__titulo">
      <a href="/condicoes-hidrologicas" title="Leia na &iacute;ntegra.">
        Condi&ccedil;&otilde;es hidrol&oacute;gicas para os pr&oacute;ximos dias no RS
      </a>
    </h2>
  </header>
  <p class="hidden-xs">N&iacute;veis entre aten&ccedil;&atilde;o e normalidade no sul do estado...</p>
</article>
<article class="conteudo-lista__item clearfix">
  <header>
    <time datetime='2026-08-26T12:42:07-0300'>26/08/2026</time>
    <h2><a href='/condicoes-meteorologicas'>Condi&ccedil;&otilde;es meteorol&oacute;gicas para os pr&oacute;ximos dias no RS</a></h2>
  </header>
  <p>Tempestades principalmente em &aacute;reas do Sul...</p>
</article>`;

const CURRENT_HYDRO_ARTICLE_HTML = `
<html><head>
  <meta property="og:image" content="http://www.defesacivil.rs.gov.br/upload/card-menor.png">
</head><body>
<article class="artigo artigo__noticia--grande">
  <header><h1>Condições hidrológicas</h1></header>
  <figure class="artigo__ilustracao">
    <a href="/upload/recortes/202608/card-hidro-GDO.png">
      <img src="/upload/recortes/202608/card-hidro-GD.png" alt="card hidro">
    </a>
  </figure>
  <div class="artigo__texto"><div><p>
    A condição atual é de estabilidade nesta quarta-feira (26/8).
    Devido à previsão de chuvas volumosas, é indicado risco de INUNDAÇÃO
    para as regiões baixas das bacias Taquari (a partir de Encantado),
    em vermelho no mapa hidrológico.
  </p></div></div>
</article>
</body></html>`;

const CURRENT_WEATHER_ARTICLE_HTML = `
<article class="artigo artigo__noticia--grande">
  <figure class="artigo__ilustracao">
    <a href="/upload/recortes/202608/card-met-GDO.png"><img src="card-met.png"></a>
  </figure>
  <div class="artigo__texto"><p>
    Na quinta-feira (27/8), há condições para tempestades.
    Na sexta-feira (28/8), segue a condição para chuva forte.
    No sábado e domingo (29/8 e 30/8), há chuva intensa e volumosa
    especialmente em áreas dos Vales e Nordeste, com tempestades severas.
  </p></div>
  <div class="conteudo-relacionado">Outro aviso que não faz parte do resumo.</div>
</article>`;

test("extrai candidatos da listagem oficial sem exigir território no resumo truncado", () => {
  const candidates = extractDefenseCivilAlertCandidates(CURRENT_LISTING_HTML);

  assert.equal(candidates.length, 2);
  assert.deepEqual(candidates[0], {
    id: "/condicoes-hidrologicas",
    title: "Condições hidrológicas para os próximos dias no RS",
    summary: "Níveis entre atenção e normalidade no sul do estado...",
    publishedAt: "2026-08-26T12:43:00-03:00",
    href: "https://www.defesacivil.rs.gov.br/condicoes-hidrologicas",
  });
});

test("artigo completo corrige falso negativo territorial e usa a última data futura", () => {
  const candidate = extractDefenseCivilAlertCandidates(CURRENT_LISTING_HTML)[1];
  const alert = parseDefenseCivilArticle(
    CURRENT_WEATHER_ARTICLE_HTML,
    candidate,
    Date.parse("2026-08-27T12:00:00-03:00"),
  );

  assert.ok(alert);
  assert.equal(alert.validUntil, "2026-08-31T02:59:59.999Z");
  assert.equal(alert.severity, "red");
  assert.match(alert.summary, /Na quinta-feira/);
  assert.doesNotMatch(alert.summary, /Outro aviso/);
  assert.equal(alert.source, "Defesa Civil RS");
  assert.equal(alert.sourceUrl, candidate.href);
  assert.equal(
    alert.imageUrl,
    "https://www.defesacivil.rs.gov.br/upload/recortes/202608/card-met-GDO.png",
  );
});

test("artigo hidrológico aceita Taquari e Encantado e usa vigência lida do card", () => {
  const candidate = extractDefenseCivilAlertCandidates(CURRENT_LISTING_HTML)[0];
  const alert = parseDefenseCivilArticle(
    CURRENT_HYDRO_ARTICLE_HTML,
    candidate,
    Date.parse("2026-08-27T12:00:00-03:00"),
    "CARD AVISO 15 — VIGÊNCIA 27/8/26 a 30/8/26 — DEFESA CIVIL",
  );

  assert.ok(alert);
  assert.equal(alert.validUntil, "2026-08-31T02:59:59.999Z");
  assert.equal(alert.severity, "red");
  assert.equal(
    alert.imageUrl,
    "https://www.defesacivil.rs.gov.br/upload/recortes/202608/card-hidro-GDO.png",
  );
});

test("vigência do card termina no fim do último dia em Brasília", () => {
  const validity = validUntilFromDefenseCivilCardText(
    "VIGÊNCIA 27/8/26 a 30/8/26",
    "2026-08-26T12:43:00-03:00",
  );
  assert.equal(validity?.toISOString(), "2026-08-31T02:59:59.999Z");
});

test("mantém o formato legado de validade explícita", () => {
  const listing = `
    <article>
      <time datetime="2026-08-27T10:00:00-0300"></time>
      <h2><a href="/alerta-legado">Defesa Civil alerta: nível vermelho em Muçum</a></h2>
      <p>Alerta válido até 18h00 do dia 30/08/2026 para o Vale do Taquari.</p>
    </article>`;
  const alerts = parseDefenseCivilAlerts(
    listing,
    Date.parse("2026-08-27T12:00:00-03:00"),
  );

  assert.equal(alerts.length, 1);
  assert.equal(alerts[0].validUntil, "2026-08-30T21:00:00.000Z");
  assert.equal(alerts[0].severity, "red");
  assert.equal(alerts[0].imageUrl, null);
  assert.equal(
    validUntilFromDefenseCivilText(
      "Válido até 18h00 do dia 30/08/2026",
      "2026-08-27T10:00:00-03:00",
    )?.toISOString(),
    "2026-08-30T21:00:00.000Z",
  );
});

test("horário sem minutos termina na hora cheia", () => {
  assert.equal(
    validUntilFromDefenseCivilText(
      "Válido até 18h do dia 30/08/2026",
      "2026-08-27T10:00:00-03:00",
    )?.toISOString(),
    "2026-08-30T21:00:00.000Z",
  );
});

test("relevância ampliada cobre as denominações territoriais esperadas", () => {
  for (const territory of [
    "Muçum",
    "Mucum",
    "bacia do Taquari-Antas",
    "bacias Taquari",
    "Encantado",
    "Vale do Taquari",
    "áreas dos Vales",
  ]) {
    assert.equal(isDefenseCivilAlertRelevant(territory), true, territory);
  }
  assert.equal(isDefenseCivilAlertRelevant("somente a região Sul"), false);
});

test("imagem externa não é aceita como imagem oficial", () => {
  assert.equal(
    extractDefenseCivilImage(
      '<meta property="og:image" content="https://example.com/card.png">',
      "https://www.defesacivil.rs.gov.br/alerta",
    ),
    null,
  );
});
