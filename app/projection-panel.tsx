"use client";

import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { PROJECTION_STATIONS, projectionIsStale, validProjection, type ProjectionStation, type StationProjection } from "@/lib/projection";

const time = (value: string) => new Date(value).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" });
const descriptions: Record<ProjectionStation, string> = {
  mucum: "O modelo aprende relações entre medições históricas de nível, vazões das hidrelétricas, chuva observada e previsões de chuva para estimar o nível em Muçum.",
  encantado: "O modelo de Encantado usa medições históricas dos níveis em Encantado e Muçum para estimar as próximas 6 horas. Cada cidade tem seu próprio modelo e sua própria régua. Chuva prevista e operação de barragens não entram diretamente neste modelo.",
  "santa-tereza": "O modelo de Santa Tereza usa medições históricas da estação na cidade e da Linha José Júlio para estimar as próximas 6 horas na régua da cidade. Chuva prevista e operação de barragens não entram diretamente neste modelo.",
};
const level = (value: number) => value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function ProjectionPanel() {
  const [station, setStation] = useState<ProjectionStation>("mucum");
  return (
    <section className="panel projection-panel" id="previsao" aria-labelledby="projection-title">
      <div className="projection-heading">
        <div><span className="projection-eyebrow">PREVISÃO DE 6 HORAS</span><h2 id="projection-title"><TrendingUp size={20} aria-hidden="true" />Previsão</h2></div>
        <span className="projection-badge">Experimental</span>
      </div>
      <div className="projection-stations" role="group" aria-label="Cidade da previsão">
        {(Object.keys(PROJECTION_STATIONS) as ProjectionStation[]).map(value => (
          <button key={value} type="button" aria-pressed={station === value} onClick={() => setStation(value)}>{PROJECTION_STATIONS[value]}</button>
        ))}
      </div>
      <ProjectionContent key={station} station={station} />
    </section>
  );
}

function ProjectionContent({ station }: { station: ProjectionStation }) {
  const city = PROJECTION_STATIONS[station];
  const [data, setData] = useState<{ projection: StationProjection | null; failed: boolean; loading: boolean; now: number }>({ projection: null, failed: false, loading: true, now: 0 });
  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    async function refresh() {
      if (pending) return;
      pending = true;
      try {
        const response = await fetch(`/api/projection?station=${station}`, { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15_000)]) });
        if (!response.ok) throw new Error("unavailable");
        const payload = await response.json();
        if (payload.projection && !validProjection(payload.projection, station)) throw new Error("invalid forecast");
        if (!controller.signal.aborted) {
          setData(previous => ({ projection: payload.projection ?? previous.projection, failed: Boolean(payload.failed), loading: false, now: Date.now() }));
        }
      } catch {
        if (!controller.signal.aborted) setData(previous => ({ ...previous, failed: true, loading: false, now: Date.now() }));
      } finally { pending = false; }
    }
    void refresh();
    const timer = setInterval(() => void refresh(), 60_000);
    return () => { controller.abort(); clearInterval(timer); };
  }, [station]);
  const projection = data.projection;
  const stale = projection && (data.failed || projectionIsStale(projection, data.now));
  const points = projection?.models[0].points.slice(0, 6) ?? [];
  const chart = projection ? [{ timestamp: projection.observation.timestamp, level: projection.observation.level }, ...points] : [];
  const min = Math.floor(Math.min(...chart.map(p => p.level)) * 2) / 2 - .25;
  const max = Math.ceil(Math.max(...chart.map(p => p.level)) * 2) / 2 + .25;
  const start = chart.length ? Date.parse(chart[0].timestamp) : 0;
  const end = chart.length ? Date.parse(chart.at(-1)!.timestamp) : 1;
  const x = (timestamp: string) => 45 + (Date.parse(timestamp) - start) / Math.max(1, end - start) * 700;
  const y = (value: number) => 170 - (value - min) / Math.max(.5, max - min) * 145;
  const line = chart.map(p => `${x(p.timestamp)},${y(p.level)}`).join(" ");
  return (
    <div aria-label={`Previsão de ${city}`} aria-busy={data.loading}>
      {!projection ? <p className="projection-empty" role="status">{data.loading ? "Carregando previsão…" : data.failed ? "Previsão temporariamente indisponível." : "Aguardando o primeiro cálculo."}</p> : (
        <>
          {stale && <p className="projection-warning" role="status">Exibindo o último cálculo disponível, de {new Date(projection.generatedAt).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" })} às {time(projection.generatedAt)}.</p>}
          {points.length ? <>
            <svg className="projection-chart" viewBox="0 0 770 205" role="img" aria-label={`Nível observado em ${city} seguido da previsão de nível para as 6 horas após a referência da rodada, em metros. Valores disponíveis na tabela abaixo.`}>
              {[min, (min + max) / 2, max].map(v => <g key={v}><line x1="45" x2="745" y1={y(v)} y2={y(v)} stroke="currentColor" opacity=".1" /><text x="35" y={y(v) + 4} textAnchor="end">{v.toFixed(1)}</text></g>)}
              <polyline points={line} fill="none" stroke="#37836b" strokeWidth="2.5" strokeDasharray="6 4" strokeLinejoin="round" />
              <circle cx={x(chart[0].timestamp)} cy={y(chart[0].level)} r="4" fill="#37836b" />
              {points.filter((_, i) => i % 3 === 0 || i === points.length - 1).map(p => <text key={p.timestamp} x={x(p.timestamp)} y="196" textAnchor="middle">{time(p.timestamp)}</text>)}
            </svg>
            <div className="projection-table-wrap" tabIndex={0} role="region" aria-label="Previsão horária; role horizontalmente para consultar os horários"><table className="projection-table"><caption className="sr-only">Previsão do nível do rio em {city}, horário de Brasília</caption><thead><tr>{points.map(p => <th key={p.timestamp} scope="col">{time(p.timestamp)}</th>)}</tr></thead><tbody><tr>{points.map(p => <td key={p.timestamp}>{level(p.level)} <span>m</span></td>)}</tr></tbody></table></div>
          </> : <p className="projection-empty">O último cálculo não contém horários futuros. Aguardando atualização.</p>}
          <details className="projection-details"><summary>Como funciona o modelo de previsão</summary><p>{descriptions[station]} A última medição disponível até a referência da rodada é o ponto de partida.</p><p>Uma nova rodada é publicada a cada hora, prevendo as 6 horas seguintes a partir do horário da rodada. Por exemplo: a rodada das 14h prevê os níveis das 15h às 20h; a das 15h prevê das 16h às 21h. O painel exibe sempre a rodada mais recente disponível. Os horários são de Brasília.</p><p>Este modelo é experimental: pode errar, principalmente em mudanças rápidas e situações pouco representadas no histórico. Os resultados ainda estão em validação.{station !== "mucum" && ` A avaliação de ${city} usa dados de 2025 e 2026; ainda não inclui as cheias extremas de 2023 e 2024.`} Não substitui alertas e orientações da Defesa Civil.</p></details>
        </>
      )}
    </div>
  );
}
