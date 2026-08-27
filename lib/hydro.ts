export type Quality = "approved" | "unverified" | "missing";

export type AnaRecord = {
  timestamp: string;
  rain: number | null;
  accumulatedRain: number | null;
  levelCm: number | null;
  discharge: number | null;
  quality: Quality;
};

export type HydroStation = {
  code: string;
  city: string;
  name: string;
  latitude: number;
  longitude: number;
  river: string;
  thresholds?: {
    attention: number;
    alert: number;
    flood: number;
  };
};

export const SACE_LEVEL_SENSORS = [
  {
    id: "sace-86510000",
    code: "86510000",
    city: "Muçum",
    name: "Sensor na Cidade de Muçum",
    csv: "https://sace.sgb.gov.br/api/dados/taquari_3_cota.csv",
  },
  {
    id: "sace-86472600",
    code: "86472600",
    city: "Santa Tereza",
    name: "Sensor na Cidade de Santa Tereza",
    csv: "https://sace.sgb.gov.br/api/dados/taquari_32_cota.csv",
  },
  {
    id: "sace-86472000",
    code: "86472000",
    city: "Santa Tereza",
    name: "Sensor na Linha José Júlio",
    csv: "https://sace.sgb.gov.br/api/dados/taquari_4_cota.csv",
  },
  {
    id: "sace-86560000",
    code: "86560000",
    city: "Guaporé",
    name: "Sensor na Linha Colombo",
    csv: "https://sace.sgb.gov.br/api/dados/taquari_55_cota.csv",
  },
  {
    id: "sace-86500000",
    code: "86500000",
    city: "Guaporé",
    name: "Sensor no Passo Carreiro",
    csv: "https://sace.sgb.gov.br/api/dados/taquari_54_cota.csv",
  },
] as const;

export const SACE_STATIONS: HydroStation[] = [
  {
    code: "02852004",
    city: "Soledade",
    name: "Auler",
    latitude: -28.8034,
    longitude: -52.38154,
    river: "Bacia Taquari-Antas",
  },
  {
    code: "02850045",
    city: "Vacaria",
    name: "Vacaria",
    latitude: -28.5175,
    longitude: -50.95361,
    river: "Bacia Taquari-Antas",
  },
  {
    code: "86495500",
    city: "Guaporé",
    name: "PCH São Paulo Barramento",
    latitude: -28.775,
    longitude: -51.8447,
    river: "Rio Carreiro",
  },
  {
    code: "02851072",
    city: "Ibiraiaras",
    name: "Ibiraiaras",
    latitude: -28.37277,
    longitude: -51.63277,
    river: "Bacia Taquari-Antas",
  },
  {
    code: "02851024",
    city: "Nova Prata",
    name: "Prata",
    latitude: -28.7561,
    longitude: -51.6283,
    river: "Bacia Taquari-Antas",
  },
  {
    code: "02851159",
    city: "Flores da Cunha",
    name: "Flores da Cunha–Antônio Prado",
    latitude: -28.9422,
    longitude: -51.1897,
    river: "Bacia Taquari-Antas",
  },
  {
    code: "86060010",
    city: "Cambará do Sul",
    name: "CGH Cambará Barramento",
    latitude: -28.9489,
    longitude: -50.0556,
    river: "Arroio Arcada",
  },
  {
    code: "86099000",
    city: "Bom Jesus",
    name: "PCH Pezzi Montante",
    latitude: -28.8047,
    longitude: -50.4936,
    river: "Rio das Antas",
  },
  {
    code: "86102000",
    city: "São Francisco de Paula",
    name: "PCH Passo do Meio Montante Tainhas",
    latitude: -28.8644,
    longitude: -50.5622,
    river: "Rio Tainhas",
  },
  {
    code: "86117000",
    city: "Vila Maria",
    name: "PCH Serra dos Cavalinhos I",
    latitude: -28.79,
    longitude: -50.6789,
    river: "Arroio do Governador",
  },
  {
    code: "86125000",
    city: "Campestre da Serra",
    name: "CGH Trabuco Jusante",
    latitude: -28.6022,
    longitude: -51.2344,
    river: "Arroio Trabuco",
  },
  {
    code: "86125050",
    city: "Muitos Capões",
    name: "PCH Morro Grande Montante",
    latitude: -28.5486,
    longitude: -51.3017,
    river: "Rio Ituim",
  },
  {
    code: "86163000",
    city: "Monte Alegre dos Campos",
    name: "PCH Serra dos Cavalinhos II Jusante",
    latitude: -28.7869,
    longitude: -50.7447,
    river: "Rio das Antas",
  },
  {
    code: "86200900",
    city: "Caxias do Sul",
    name: "PCH Criúva Barramento",
    latitude: -28.9653,
    longitude: -50.7989,
    river: "Lajeado Grande",
  },
  {
    code: "86280500",
    city: "São Marcos",
    name: "PCH Rio São Marcos Barramento",
    latitude: -29.0367,
    longitude: -51.0956,
    river: "Arroio São Marcos",
  },
  {
    code: "86298000",
    city: "Antônio Prado",
    name: "UHE Castro Alves RS-122",
    latitude: -28.9414,
    longitude: -51.1892,
    river: "Rio das Antas",
  },
  {
    code: "86403000",
    city: "André da Rocha",
    name: "PCH Jardim Jusante",
    latitude: -28.5692,
    longitude: -51.4064,
    river: "Rio Turvo",
  },
  {
    code: "86448000",
    city: "Veranópolis",
    name: "UHE Monte Claro Barramento",
    latitude: -29.0292,
    longitude: -51.5219,
    river: "Rio das Antas",
  },
  {
    code: "86450000",
    city: "Bento Gonçalves",
    name: "UHE Monte Claro Jusante",
    latitude: -29.075,
    longitude: -51.5239,
    river: "Rio das Antas",
  },
  {
    code: "86479000",
    city: "São Domingos do Sul",
    name: "PCH Caçador Ponte São Domingos",
    latitude: -28.5792,
    longitude: -51.8686,
    river: "Rio São Domingos",
  },
  {
    code: "86504900",
    city: "Vista Alegre do Prata",
    name: "PCH Autódromo Jusante",
    latitude: -28.8817,
    longitude: -51.7897,
    river: "Rio Carreiro",
  },
  {
    code: "86505500",
    city: "Dois Lajeados",
    name: "PCH Linha Emília Jusante",
    latitude: -28.9414,
    longitude: -51.7694,
    river: "Rio Carreiro",
  },
  {
    code: "86520000",
    city: "Marau",
    name: "PCH Capigui Barramento",
    latitude: -28.3511,
    longitude: -52.2147,
    river: "Rio Capigui",
  },
  {
    code: "86743800",
    city: "São José do Herval",
    name: "PCH Rastro de Auto Barramento",
    latitude: -29.0533,
    longitude: -52.2194,
    river: "Rio Forqueta",
  },
  {
    code: "86743900",
    city: "Putinga",
    name: "PCH Salto Forqueta Barramento",
    latitude: -29.0814,
    longitude: -52.2083,
    river: "Rio Forqueta",
  },
  {
    code: "86744650",
    city: "Pouso Novo",
    name: "PCH Vale do Leite Jusante",
    latitude: -29.1867,
    longitude: -52.1756,
    river: "Rio Forqueta",
  },
  {
    code: "86780000",
    city: "Travesseiro",
    name: "Barra do Fão",
    latitude: -29.2239,
    longitude: -52.1622,
    river: "Rio Forqueta",
  },
  {
    code: "86410800",
    city: "Protásio Alves",
    name: "PCH da Ilha Afluente",
    latitude: -28.7983,
    longitude: -51.4744,
    river: "Arroio Primavera",
  },
  {
    code: "86447000",
    city: "Nova Roma do Sul",
    name: "UHE Monte Claro Balsa do Prata",
    latitude: -28.9714,
    longitude: -51.4611,
    river: "Rio das Antas",
  },
  {
    code: "86471000",
    city: "Cotiporã",
    name: "UHE 14 de Julho Jusante",
    latitude: -29.0797,
    longitude: -51.6814,
    river: "Rio das Antas",
  },
  {
    code: "86488000",
    city: "Serafina Corrêa",
    name: "PCH Caçador Montante",
    latitude: -28.6847,
    longitude: -51.8506,
    river: "Rio Carreiro",
  },
  {
    code: "86493000",
    city: "Nova Bassano",
    name: "PCH Boa Fé Barramento",
    latitude: -28.7464,
    longitude: -51.8536,
    river: "Rio Carreiro",
  },
  {
    code: "86160000",
    city: "Jaquirana",
    name: "Passo Tainhas",
    latitude: -28.88269,
    longitude: -50.39594,
    river: "Rio Tainhas",
  },
  {
    code: "86472000",
    city: "Santa Tereza",
    name: "Linha José Júlio",
    latitude: -29.09807,
    longitude: -51.69956,
    river: "Rio das Antas",
  },
  {
    code: "86510000",
    city: "Muçum",
    name: "Muçum",
    latitude: -29.16694,
    longitude: -51.86722,
    river: "Rio Taquari",
    thresholds: { attention: 5, alert: 9, flood: 18 },
  },
  {
    code: "86720000",
    city: "Encantado",
    name: "Encantado",
    latitude: -29.23519,
    longitude: -51.85507,
    river: "Rio Taquari",
  },
  {
    code: "86879300",
    city: "Estrela",
    name: "Estrela",
    latitude: -29.47349,
    longitude: -51.96281,
    river: "Rio Taquari",
  },
  {
    code: "86881000",
    city: "Bom Retiro do Sul",
    name: "Bom Retiro do Sul — Montante",
    latitude: -29.6081,
    longitude: -51.9511,
    river: "Rio Taquari",
  },
  {
    code: "86895000",
    city: "Venâncio Aires",
    name: "Porto Mariante",
    latitude: -29.69958,
    longitude: -51.9665,
    river: "Rio Taquari",
  },
  {
    code: "86950000",
    city: "Taquari",
    name: "Taquari",
    latitude: -29.80688,
    longitude: -51.87659,
    river: "Rio Taquari",
  },
];

const MUCUM_UPSTREAM_RAIN_STATION_CODES = new Set([
  "02850045",
  "86495500",
  "02851072",
  "02851024",
  "02851159",
  "86060010",
  "86099000",
  "86102000",
  "86117000",
  "86125000",
  "86125050",
  "86163000",
  "86200900",
  "86280500",
  "86298000",
  "86403000",
  "86448000",
  "86450000",
  "86479000",
  "86504900",
  "86505500",
  "86520000",
  "86410800",
  "86447000",
  "86471000",
  "86488000",
  "86493000",
  "86160000",
  "86472000",
  "86510000",
]);

export const MUCUM_UPSTREAM_RAIN_STATIONS = SACE_STATIONS.filter((station) =>
  MUCUM_UPSTREAM_RAIN_STATION_CODES.has(station.code),
);

export function decodeEntities(value: string) {
  return value
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#039;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)));
}

export function stripTags(value: string) {
  return decodeEntities(value.replace(/<br\s*\/?>/gi, " ").replace(/<[^>]+>/g, " "))
    .replace(/\s+/g, " ")
    .trim();
}

export function parseXmlRows(xml: string, rowTag: string) {
  const rows: Record<string, string>[] = [];
  const rowRegex = new RegExp(`<${rowTag}\\b[^>]*>([\\s\\S]*?)<\\/${rowTag}>`, "gi");
  for (const match of xml.matchAll(rowRegex)) {
    const row: Record<string, string> = {};
    const fieldRegex = /<([A-Za-z0-9_-]+)(?:\s[^>]*)?>([\s\S]*?)<\/\1>|<([A-Za-z0-9_-]+)(?:\s[^>]*)?\/>/g;
    for (const field of match[1].matchAll(fieldRegex)) {
      row[field[1] || field[3]] = stripTags(field[2] || "");
    }
    rows.push(row);
  }
  return rows;
}

export function parseAnaRecords(xml: string): AnaRecord[] {
  return parseXmlRows(xml, "DadosHidrometereologicos")
    .map((row) => {
      const number = (value?: string) => {
        if (!value?.trim()) return null;
        const parsed = Number(value.replace(",", "."));
        return Number.isFinite(parsed) ? parsed : null;
      };
      const approved =
        row.CQ_NivelFinal === "Dado aprovado" ||
        row.CQ_ChuvaFinal === "Dado aprovado";
      return {
        timestamp: row.DataHora ? `${row.DataHora.replace(" ", "T")}-03:00` : "",
        rain: number(row.ChuvaFinal),
        accumulatedRain: number(row.ChuvaAcumAdotada),
        levelCm: number(row.NivelFinal),
        discharge: number(row.VazaoFinal),
        quality: row.DataHora ? (approved ? "approved" : "unverified") : "missing",
      } satisfies AnaRecord;
    })
    .filter((row) => Boolean(row.timestamp))
    .sort((a, b) => Date.parse(b.timestamp) - Date.parse(a.timestamp));
}

export function severityFor(
  levelMeters: number | null,
  thresholds: NonNullable<HydroStation["thresholds"]>,
) {
  if (levelMeters === null) return "unavailable" as const;
  if (levelMeters >= thresholds.flood) return "flood" as const;
  if (levelMeters >= thresholds.alert) return "alert" as const;
  if (levelMeters >= thresholds.attention) return "attention" as const;
  return "normal" as const;
}

export function accumulatedRain(
  records: AnaRecord[],
  hours: number,
  nowMs = Date.now(),
) {
  const cutoff = nowMs - hours * 60 * 60 * 1000;
  const values = records
    .filter((row) => {
      const timestamp = Date.parse(row.timestamp);
      return timestamp >= cutoff && timestamp <= nowMs;
    })
    .map((row) => row.rain)
    .filter((rain): rain is number => rain !== null && rain >= 0);
  return values.length
    ? Number(values.reduce((sum, value) => sum + value, 0).toFixed(1))
    : null;
}

export function parseSaceLevelRows(csv: string) {
  const readings: Array<{
    timestamp: string;
    level: number;
    levelCm: number;
  }> = [];

  for (const line of csv.split(/\r?\n/)) {
    const match = line
      .trim()
      .match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2});\s*(-?\d+(?:[.,]\d+)?)$/);
    if (!match) continue;

    const levelCm = Number(match[3].replace(",", "."));
    const timestamp = `${match[1]}T${match[2]}-03:00`;
    const timestampMs = Date.parse(timestamp);
    if (!Number.isFinite(levelCm) || !Number.isFinite(timestampMs)) continue;

    readings.push({
      timestamp,
      level: Number((levelCm / 100).toFixed(2)),
      levelCm,
    });
  }

  return readings
    .filter(
      (reading, index, all) =>
        index ===
        all.findIndex((candidate) => candidate.timestamp === reading.timestamp),
    )
    .sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));
}

export function parseSaceLevelCsv(csv: string) {
  return parseSaceLevelRows(csv).at(-1) ?? null;
}

export function saoPauloDate(date: Date) {
  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}
