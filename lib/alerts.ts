export type DefenseCivilAlert = {
  id: string;
  title: string;
  summary: string;
  publishedAt: string;
  validUntil: string;
  severity: "yellow" | "orange" | "red";
  href: string;
};

const DEFENSE_CIVIL_HOST = "www.defesacivil.rs.gov.br";

function stripTags(value: string) {
  const namedEntities: Record<string, string> = {
    aacute: "á",
    acirc: "â",
    agrave: "à",
    atilde: "ã",
    ccedil: "ç",
    eacute: "é",
    ecirc: "ê",
    iacute: "í",
    oacute: "ó",
    ocirc: "ô",
    otilde: "õ",
    uacute: "ú",
  };
  return value
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#039;", "'")
    .replace(/&([a-z]+);/gi, (entity, name) =>
      namedEntities[name.toLocaleLowerCase()] || entity,
    )
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/\s+/g, " ")
    .trim();
}

function severityForAlert(text: string): DefenseCivilAlert["severity"] {
  const normalized = text.toLocaleLowerCase("pt-BR");
  if (normalized.includes("vermelho") || normalized.includes("severa")) return "red";
  if (normalized.includes("laranja")) return "orange";
  return "yellow";
}

export function extractDefenseCivilImage(html: string, pageUrl: string) {
  const articleImage = html.match(
    /<figure\b[^>]*class=["'][^"']*\bartigo__ilustracao\b[^"']*["'][^>]*>[\s\S]*?<a\b[^>]*href=["']([^"']+)["']/i,
  )?.[1];
  let socialImage: string | undefined;
  for (const match of html.matchAll(/<meta\b[^>]*>/gi)) {
    const tag = match[0];
    if (!/\bproperty=["']og:image(?::secure_url)?["']/i.test(tag)) continue;
    socialImage = tag.match(/\bcontent=["']([^"']+)["']/i)?.[1];
    if (socialImage) break;
  }

  const source = (articleImage || socialImage)?.replaceAll("&amp;", "&");
  if (!source) return null;

  try {
    const imageUrl = new URL(source, pageUrl);
    if (imageUrl.protocol !== "https:" || imageUrl.hostname !== DEFENSE_CIVIL_HOST) {
      return null;
    }
    return imageUrl.toString();
  } catch {
    return null;
  }
}

function validUntilFromText(text: string) {
  const match = text.match(
    /v[aá]lid[oa]\s+at[eé]\s+(?:[àa]s?\s*)?(\d{1,2})h(\d{2})\s+(?:do\s+dia\s+)?(\d{2})\/(\d{2})\/(\d{4})/i,
  );
  if (!match) return null;
  const [, hour, minute, day, month, year] = match;
  const value = new Date(`${year}-${month}-${day}T${hour.padStart(2, "0")}:${minute}:00-03:00`);
  return Number.isNaN(value.getTime()) ? null : value;
}

export function parseDefenseCivilAlerts(body: string, nowMs = Date.now()) {
  const relevantTerritory = /\b(mu[çc]um|vale do taquari)\b/i;
  const articles = [...body.matchAll(/<article\b[^>]*>([\s\S]*?)<\/article>/gi)];

  const parsed = articles.flatMap((match) => {
    const article = match[1];
    const time = article.match(/<time\b[^>]*datetime="([^"]+)"/i)?.[1];
    const titleMatch = article.match(
      /<h2\b[^>]*>[\s\S]*?<a\b[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/h2>/i,
    );
    const summaryMatch = article.match(/<p\b[^>]*>([\s\S]*?)<\/p>/i);
    if (!time || !titleMatch) return [];

    const title = stripTags(titleMatch[2]);
    const summary = stripTags(summaryMatch?.[1] || "");
    const combined = `${title} ${summary}`;
    const validUntil = validUntilFromText(combined);
    if (!relevantTerritory.test(combined) || !validUntil || validUntil.getTime() <= nowMs) {
      return [];
    }

    const path = titleMatch[1];
    return [{
      id: path,
      title,
      summary,
      publishedAt: time.replace(/([+-]\d{2})(\d{2})$/, "$1:$2"),
      validUntil: validUntil.toISOString(),
      severity: severityForAlert(combined),
      href: new URL(path, "https://www.defesacivil.rs.gov.br").toString(),
    } satisfies DefenseCivilAlert];
  });

  const unique = new Map<string, DefenseCivilAlert>();
  for (const alert of parsed) {
    const key = `${alert.title.toLocaleLowerCase("pt-BR")}|${alert.validUntil}`;
    const existing = unique.get(key);
    if (
      !existing ||
      Date.parse(alert.publishedAt) > Date.parse(existing.publishedAt)
    ) {
      unique.set(key, alert);
    }
  }
  return [...unique.values()].sort(
    (left, right) =>
      Date.parse(right.publishedAt) - Date.parse(left.publishedAt),
  );
}
