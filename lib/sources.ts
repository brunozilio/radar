function stripTags(value: string) {
  return value
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#039;", "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)))
    .replace(/\s+/g, " ")
    .trim();
}

export const CERAN_PLANT_SOURCES = {
  castro: {
    id: "castro",
    name: "UHE Castro Alves",
    source: "https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHCA.php",
  },
  monte: {
    id: "monte",
    name: "UHE Monte Claro",
    source: "https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHMC.php",
  },
  julho: {
    id: "julho",
    name: "UHE 14 de Julho",
    source: "https://ceran.com.br/dados_hidrologicos/dados_hidrologicos_UHQJ.php",
  },
} as const;

export type CeranPlantId = keyof typeof CERAN_PLANT_SOURCES;

export function parseRadarTimestampText(text: string) {
  const match = text.match(
    /(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}:\d{2}:\d{2})/,
  );
  if (!match) return null;
  const timestamp = `${match[3]}-${match[2]}-${match[1]}T${match[4]}-03:00`;
  return Number.isFinite(Date.parse(timestamp))
    ? new Date(timestamp).toISOString()
    : null;
}

export function inmetSatelliteTimestamp(date: string, hour: string) {
  const dateMatch = date.match(/^(\d{4}-\d{2}-\d{2})/);
  if (!dateMatch || !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(hour)) return null;
  const timestamp = `${dateMatch[1]}T${hour}:00Z`;
  return Number.isFinite(Date.parse(timestamp))
    ? new Date(timestamp).toISOString()
    : null;
}

export function cptecSatelliteTimestamp(date: string, time: string) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    !/^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$/.test(time)
  ) {
    return null;
  }
  const timestamp = `${date}T${time}Z`;
  return Number.isFinite(Date.parse(timestamp))
    ? new Date(timestamp).toISOString()
    : null;
}

function ceranTimestamp(value: string) {
  const match = value.match(
    /^(\d{2})\/(\d{2})\/(\d{4})\s+(\d{2}:\d{2}:\d{2})$/,
  );
  return match
    ? `${match[3]}-${match[2]}-${match[1]}T${match[4]}-03:00`
    : value;
}

export function parseCeranTable(html: string) {
  const rows = [...html.matchAll(/<tr\b[^>]*>([\s\S]*?)<\/tr>/gi)].slice(1);
  return rows
    .map((row) => {
      const cells = [...row[1].matchAll(/<td\b[^>]*>([\s\S]*?)<\/td>/gi)].map(
        (cell) => stripTags(cell[1]),
      );
      if (cells.length < 8) return null;
      const numeric = cells
        .slice(1)
        .map((value) => Number(value.replace(",", ".")));
      if (numeric.some((value) => !Number.isFinite(value))) return null;
      const [
        upstreamLevel,
        downstreamLevel,
        inflow,
        turbined,
        spilled,
        residual,
        outflow,
      ] = numeric;
      return {
        timestamp: ceranTimestamp(cells[0]),
        upstreamLevel,
        downstreamLevel,
        inflow,
        turbined,
        spilled,
        residual,
        outflow,
        status: spilled > 0 ? "Vertendo" : "Normal",
      };
    })
    .filter((row): row is NonNullable<typeof row> => Boolean(row));
}

export function parseSaceBulletins(html: string) {
  const base = "https://www.sgb.gov.br/sace/";
  return [
    ...html.matchAll(
      /<a\s+href=['"]([^'"]*boletins\/Taquari\/[^'"]+\.pdf)['"][^>]*>([\s\S]*?)<\/a>/gi,
    ),
  ].map((match, index) => {
    const title = stripTags(match[2]);
    const dateMatch = title.match(
      /(\d{2})\/(\d{2})\/(\d{4})\s*\((\d{2})h\)/,
    );
    const href = new URL(match[1].replaceAll(" ", "%20"), base).toString();
    return {
      id: href,
      title,
      date: dateMatch
        ? `${dateMatch[3]}-${dateMatch[2]}-${dateMatch[1]}T${dateMatch[4]}:00:00-03:00`
        : null,
      status: index === 0 ? "Último boletim" : "Boletim oficial",
      href,
      latest: index === 0,
    };
  });
}

export function epagriRadarTimestamp(fileName: string) {
  const match = fileName.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/);
  if (!match) return null;
  const [, year, month, day, hour, minute, second] = match;
  const timestamp = new Date(
    `${year}-${month}-${day}T${hour}:${minute}:${second}.000Z`,
  );
  return Number.isNaN(timestamp.getTime()) ? null : timestamp.toISOString();
}
