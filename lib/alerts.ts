export type DefenseCivilAlertCandidate = {
  id: string;
  title: string;
  summary: string;
  publishedAt: string;
  href: string;
};

export type DefenseCivilAlert = DefenseCivilAlertCandidate & {
  validUntil: string;
  severity: "yellow" | "orange" | "red";
  source: "Defesa Civil RS";
  sourceUrl: string;
  imageUrl: string | null;
};

const DEFENSE_CIVIL_ORIGIN = "https://www.defesacivil.rs.gov.br";
const DEFENSE_CIVIL_HOSTS = new Set([
  "defesacivil.rs.gov.br",
  "www.defesacivil.rs.gov.br",
]);

function decodeHtmlEntities(value: string) {
  const namedEntities: Record<string, string> = {
    aacute: "á",
    acirc: "â",
    agrave: "à",
    atilde: "ã",
    ccedil: "ç",
    eacute: "é",
    ecirc: "ê",
    iacute: "í",
    nbsp: " ",
    oacute: "ó",
    ocirc: "ô",
    otilde: "õ",
    quot: '"',
    uacute: "ú",
  };
  return value
    .replaceAll("&amp;", "&")
    .replaceAll("&#039;", "'")
    .replace(/&([a-z]+);/gi, (entity, name) =>
      namedEntities[name.toLocaleLowerCase()] || entity,
    )
    .replace(/&#x([0-9a-f]+);/gi, (_, code) =>
      String.fromCodePoint(Number.parseInt(code, 16)),
    )
    .replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)));
}

function stripTags(value: string) {
  return decodeHtmlEntities(
    value
      .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, " ")
      .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, " ")
      .replace(/<br\s*\/?>/gi, " ")
      .replace(/<[^>]+>/g, " "),
  )
    .replace(/\s+/g, " ")
    .trim();
}

function attributeFromTag(tag: string, name: string) {
  const quoted = tag.match(
    new RegExp(`\\b${name}\\s*=\\s*(["'])([\\s\\S]*?)\\1`, "i"),
  )?.[2];
  if (quoted !== undefined) return decodeHtmlEntities(quoted);
  return decodeHtmlEntities(
    tag.match(new RegExp(`\\b${name}\\s*=\\s*([^\\s>]+)`, "i"))?.[1] || "",
  );
}

function normalizePublishedAt(value: string) {
  return value.trim().replace(/([+-]\d{2})(\d{2})$/, "$1:$2");
}

function officialDefenseCivilUrl(value: string, pageUrl = DEFENSE_CIVIL_ORIGIN) {
  try {
    const url = new URL(decodeHtmlEntities(value), pageUrl);
    if (!DEFENSE_CIVIL_HOSTS.has(url.hostname.toLocaleLowerCase())) return null;
    if (url.protocol === "http:") url.protocol = "https:";
    if (url.protocol !== "https:") return null;
    return url;
  } catch {
    return null;
  }
}

function severityForAlert(text: string): DefenseCivilAlert["severity"] {
  const normalized = text.toLocaleLowerCase("pt-BR");
  if (
    normalized.includes("vermelho") ||
    normalized.includes("severa") ||
    normalized.includes("severo")
  ) {
    return "red";
  }
  if (normalized.includes("laranja")) return "orange";
  return "yellow";
}

function articleHtmlFromPage(html: string) {
  return (
    html.match(
      /<article\b(?=[^>]*\bclass=["'][^"']*\bartigo__noticia(?:--[^\s"']+)?\b[^"']*["'])[^>]*>[\s\S]*?<\/article>/i,
    )?.[0] || html
  );
}

function balancedDivContent(html: string, contentStart: number) {
  const divTags = /<\/?div\b[^>]*>/gi;
  divTags.lastIndex = contentStart;
  let depth = 1;
  for (let tag = divTags.exec(html); tag; tag = divTags.exec(html)) {
    if (/^<\/div/i.test(tag[0])) {
      depth -= 1;
      if (depth === 0) return html.slice(contentStart, tag.index);
    } else if (!/\/>$/.test(tag[0])) {
      depth += 1;
    }
  }
  return html.slice(contentStart);
}

function articleTextFromPage(html: string) {
  const article = articleHtmlFromPage(html);
  const textContainer = article.match(
    /<div\b[^>]*class=["'][^"']*\bartigo__texto\b[^"']*["'][^>]*>/i,
  );
  if (!textContainer || textContainer.index === undefined) return stripTags(article);
  const contentStart = textContainer.index + textContainer[0].length;
  return stripTags(balancedDivContent(article, contentStart));
}

function endOfDay(day: number, month: number, year: number) {
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  const value = new Date(
    `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day
      .toString()
      .padStart(2, "0")}T23:59:59.999-03:00`,
  );
  if (Number.isNaN(value.getTime())) return null;

  // Date normaliza valores inválidos como 31/02; confirme o calendário local.
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Sao_Paulo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value);
  const parsed = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  if (
    Number(parsed.year) !== year ||
    Number(parsed.month) !== month ||
    Number(parsed.day) !== day
  ) {
    return null;
  }
  return value;
}

function inferredYearDate(
  day: number,
  month: number,
  yearText: string | undefined,
  publishedAt: Date,
) {
  if (yearText) {
    const parsedYear = Number(yearText);
    const year = yearText.length === 2 ? 2000 + parsedYear : parsedYear;
    return endOfDay(day, month, year);
  }

  const publishedYear = Number(
    new Intl.DateTimeFormat("en", {
      timeZone: "America/Sao_Paulo",
      year: "numeric",
    }).format(publishedAt),
  );
  const possibilities = [publishedYear - 1, publishedYear, publishedYear + 1]
    .map((year) => endOfDay(day, month, year))
    .filter((date): date is Date => date !== null);
  return possibilities.sort(
    (left, right) =>
      Math.abs(left.getTime() - publishedAt.getTime()) -
      Math.abs(right.getTime() - publishedAt.getTime()),
  )[0] || null;
}

function datesFromText(text: string, publishedAt: Date) {
  return [...text.matchAll(/\b(\d{1,2})\s*\/\s*(\d{1,2})(?:\s*\/\s*(\d{2}|\d{4}))?\b/g)]
    .map((match) =>
      inferredYearDate(
        Number(match[1]),
        Number(match[2]),
        match[3],
        publishedAt,
      ),
    )
    .filter((date): date is Date => date !== null);
}

export function isDefenseCivilAlertRelevant(text: string) {
  const normalized = text.normalize("NFC");
  return [
    /\bmu[çc]um\b/iu,
    /\bbacias?\s+(?:(?:do|dos)\s+)?(?:rio\s+)?taquari(?:\s*[-–—/]\s*antas)?\b/iu,
    /\btaquari\s*[-–—/]\s*antas\b/iu,
    /\bencantado\b/iu,
    /\bvales?\s+(?:do\s+)?taquari\b/iu,
    /\bvales\b/iu,
  ].some((pattern) => pattern.test(normalized));
}

export function extractDefenseCivilImage(html: string, pageUrl: string) {
  const article = articleHtmlFromPage(html);
  const imageCandidates: string[] = [];
  for (const figureMatch of article.matchAll(
    /<figure\b[^>]*class=["'][^"']*\bartigo__ilustracao\b[^"']*["'][^>]*>[\s\S]*?<\/figure>/gi,
  )) {
    const figure = figureMatch[0];
    const anchorTag = figure.match(/<a\b[^>]*>/i)?.[0];
    const imageTag = figure.match(/<img\b[^>]*>/i)?.[0];
    const source =
      (anchorTag && attributeFromTag(anchorTag, "href")) ||
      (imageTag && attributeFromTag(imageTag, "src"));
    if (source) imageCandidates.push(source);
  }

  for (const metaMatch of html.matchAll(/<meta\b[^>]*>/gi)) {
    const tag = metaMatch[0];
    const property = attributeFromTag(tag, "property").toLocaleLowerCase();
    if (property !== "og:image" && property !== "og:image:secure_url") continue;
    const source = attributeFromTag(tag, "content");
    if (source) imageCandidates.push(source);
  }

  for (const source of imageCandidates) {
    const imageUrl = officialDefenseCivilUrl(source, pageUrl);
    if (imageUrl) return imageUrl.toString();
  }
  return null;
}

export function validUntilFromDefenseCivilText(
  text: string,
  publishedAt: string,
) {
  const published = new Date(normalizePublishedAt(publishedAt));
  if (Number.isNaN(published.getTime())) return null;

  const timeThenDate = text.match(
    /v[aá]lid[oa]\s+at[eé]\s+(?:[àa]s?\s*)?(\d{1,2})(?:h|:)(\d{2})?\s*(?:h(?:oras?)?)?\s*(?:do\s+dia\s+|de\s+)?(\d{1,2})\s*\/\s*(\d{1,2})\s*\/\s*(\d{4}|\d{2})\b/iu,
  );
  const dateThenTime = text.match(
    /v[aá]lid[oa]\s+at[eé]\s+(?:o\s+dia\s+)?(\d{1,2})\s*\/\s*(\d{1,2})\s*\/\s*(\d{4}|\d{2})\b(?:\s+(?:[àa]s?\s*)?(\d{1,2})(?:h|:)(\d{2})?)?/iu,
  );
  if (timeThenDate || dateThenTime) {
    const day = Number(timeThenDate?.[3] || dateThenTime?.[1]);
    const month = Number(timeThenDate?.[4] || dateThenTime?.[2]);
    const yearText = timeThenDate?.[5] || dateThenTime?.[3];
    const end = inferredYearDate(day, month, yearText, published);
    if (!end) return null;
    const hourText = timeThenDate?.[1] || dateThenTime?.[4];
    const minuteText = timeThenDate?.[2] || dateThenTime?.[5];
    const hour = Number(hourText || 23);
    const minute = Number(minuteText ?? (hourText ? 0 : 59));
    if (hour > 23 || minute > 59) return null;
    const year = Number(
      new Intl.DateTimeFormat("en", {
        timeZone: "America/Sao_Paulo",
        year: "numeric",
      }).format(end),
    );
    const value = new Date(
      `${year.toString().padStart(4, "0")}-${month.toString().padStart(2, "0")}-${day
        .toString()
        .padStart(2, "0")}T${hour.toString().padStart(2, "0")}:${minute
        .toString()
        .padStart(2, "0")}:00-03:00`,
    );
    return Number.isNaN(value.getTime()) ? null : value;
  }

  const publishedParts = Object.fromEntries(
    new Intl.DateTimeFormat("en-CA", {
      timeZone: "America/Sao_Paulo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    })
      .formatToParts(published)
      .map((part) => [part.type, part.value]),
  );
  const publishedDayEnd = endOfDay(
    Number(publishedParts.day),
    Number(publishedParts.month),
    Number(publishedParts.year),
  );
  const futureDates = datesFromText(text, published).filter(
    (date) => !publishedDayEnd || date.getTime() > publishedDayEnd.getTime(),
  );
  if (!futureDates.length) return null;
  return new Date(Math.max(...futureDates.map((date) => date.getTime())));
}

export function validUntilFromDefenseCivilCardText(
  ocrText: string,
  publishedAt: string,
) {
  const published = new Date(normalizePublishedAt(publishedAt));
  if (Number.isNaN(published.getTime())) return null;

  const normalized = ocrText.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  const start = normalized.search(/\bVIGENCIA\b/i);
  if (start < 0) return null;
  const validityText = normalized.slice(start, start + 240);
  const dates = datesFromText(validityText, published);
  return dates.length ? dates[dates.length - 1] : null;
}

export function extractDefenseCivilAlertCandidates(body: string) {
  const candidates: DefenseCivilAlertCandidate[] = [];
  for (const match of body.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/gi)) {
    const article = match[1];
    const timeTag = article.match(/<time\b[^>]*>/i)?.[0];
    const titleBlock = article.match(/<h[1-3]\b[^>]*>[\s\S]*?<\/h[1-3]>/i)?.[0];
    const anchorTag = titleBlock?.match(/<a\b[^>]*>/i)?.[0];
    if (!timeTag || !titleBlock || !anchorTag) continue;

    const publishedAt = normalizePublishedAt(attributeFromTag(timeTag, "datetime"));
    const officialUrl = officialDefenseCivilUrl(attributeFromTag(anchorTag, "href"));
    if (!officialUrl || Number.isNaN(Date.parse(publishedAt))) continue;

    const title = stripTags(titleBlock);
    const summary = stripTags(article.match(/<p\b[^>]*>([\s\S]*?)<\/p>/i)?.[1] || "");
    if (!title) continue;
    candidates.push({
      id: officialUrl.pathname,
      title,
      summary,
      publishedAt,
      href: officialUrl.toString(),
    });
  }

  const unique = new Map<string, DefenseCivilAlertCandidate>();
  for (const candidate of candidates) {
    const existing = unique.get(candidate.id);
    if (!existing || Date.parse(candidate.publishedAt) > Date.parse(existing.publishedAt)) {
      unique.set(candidate.id, candidate);
    }
  }
  return [...unique.values()].sort(
    (left, right) => Date.parse(right.publishedAt) - Date.parse(left.publishedAt),
  );
}

export function parseDefenseCivilArticle(
  articleHtml: string,
  candidate: DefenseCivilAlertCandidate,
  nowMs = Date.now(),
  cardText?: string,
) {
  const articleText = articleTextFromPage(articleHtml);
  const combined = `${candidate.title} ${candidate.summary} ${articleText}`;
  if (!isDefenseCivilAlertRelevant(combined)) return null;

  const validUntil =
    (cardText
      ? validUntilFromDefenseCivilCardText(cardText, candidate.publishedAt)
      : null) ||
    validUntilFromDefenseCivilText(articleText, candidate.publishedAt);
  if (!validUntil || validUntil.getTime() <= nowMs) return null;

  const imageUrl = extractDefenseCivilImage(articleHtml, candidate.href);
  return {
    ...candidate,
    summary: articleText || candidate.summary,
    validUntil: validUntil.toISOString(),
    severity: severityForAlert(`${combined} ${cardText || ""}`),
    source: "Defesa Civil RS",
    sourceUrl: candidate.href,
    imageUrl,
  } satisfies DefenseCivilAlert;
}

// Compatibilidade com o coletor antigo e fixtures no formato legado, que
// continham território e validade diretamente no resumo da listagem.
export function parseDefenseCivilAlerts(body: string, nowMs = Date.now()) {
  const alerts = extractDefenseCivilAlertCandidates(body).flatMap((candidate) => {
    const combined = `${candidate.title} ${candidate.summary}`;
    const validUntil = validUntilFromDefenseCivilText(
      combined,
      candidate.publishedAt,
    );
    if (
      !isDefenseCivilAlertRelevant(combined) ||
      !validUntil ||
      validUntil.getTime() <= nowMs
    ) {
      return [];
    }
    return [{
      ...candidate,
      validUntil: validUntil.toISOString(),
      severity: severityForAlert(combined),
      source: "Defesa Civil RS",
      sourceUrl: candidate.href,
      imageUrl: null,
    } satisfies DefenseCivilAlert];
  });

  const unique = new Map<string, DefenseCivilAlert>();
  for (const alert of alerts) {
    const key = `${alert.title.toLocaleLowerCase("pt-BR")}|${alert.validUntil}`;
    const existing = unique.get(key);
    if (!existing || Date.parse(alert.publishedAt) > Date.parse(existing.publishedAt)) {
      unique.set(key, alert);
    }
  }
  return [...unique.values()].sort(
    (left, right) => Date.parse(right.publishedAt) - Date.parse(left.publishedAt),
  );
}
