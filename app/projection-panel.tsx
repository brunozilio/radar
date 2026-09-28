"use client";

import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";
import { HYDROMETRIC_MODEL_ID, projectionContradictedByObservation, projectionIsStale, readCurrentMucumObservation, validProjection, type CurrentMucumObservation, type ProjectionRefreshState, type StationProjection } from "@/lib/projection";

const time = (value: string) => new Date(value).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" });
const dateTime = (value: string) => `${new Date(value).toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit" })} às ${time(value)}`;
function forecastPeriod(points: { timestamp: string }[]) {
  if (!points.length) return "";
  if (points.length === 1) return `para ${dateTime(points[0].timestamp)}`;
  return `de ${dateTime(points[0].timestamp)} a ${dateTime(points.at(-1)!.timestamp)}`;
}
const level = (value: number) => value.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function readRefreshState(value: unknown): ProjectionRefreshState | null {
  if (!value || typeof value !== "object") return null;
  const state = value as ProjectionRefreshState;
  if (!["published", "waiting_for_data", "already_calculated", "failed"].includes(state.status) ||
      typeof state.checkedAt !== "string" || !Number.isFinite(Date.parse(state.checkedAt))) return null;
  const validTime = (timestamp: unknown) => typeof timestamp === "string" && Number.isFinite(Date.parse(timestamp)) ? timestamp : undefined;
  return {
    status: state.status, checkedAt: state.checkedAt,
    referenceAt: validTime(state.referenceAt), checkedReferenceAt: validTime(state.checkedReferenceAt),
    generatedAt: validTime(state.generatedAt),
    missing: Array.isArray(state.missing) ? state.missing.filter((reason): reason is string => typeof reason === "string") : [],
  };
}

function ProjectionRefreshNotice({ refresh, failed }: { refresh: ProjectionRefreshState | null; failed: boolean }) {
  const checked = refresh ? ` Última verificação registrada: ${dateTime(refresh.checkedAt)} (Brasília).` : "";
  if (failed || refresh?.status === "failed") return <p className="projection-warning" role="status">Não foi possível atualizar a previsão.{checked}</p>;
  if (!refresh || refresh.status === "waiting_for_data") return null;
  return <p className="projection-details">Última verificação: {dateTime(refresh.checkedAt)} (Brasília).</p>;
}

export default function ProjectionPanel() {
  return (
    <section className="panel projection-panel" id="previsao" aria-labelledby="projection-title">
      <div className="projection-heading">
        <div><span className="projection-eyebrow">PREVISÃO DE ATÉ 6 HORAS</span><h2 id="projection-title"><TrendingUp size={20} aria-hidden="true" />Previsão de Muçum</h2></div>
        <span className="projection-badge">Experimental</span>
      </div>
      <ProjectionContent />
    </section>
  );
}

function ProjectionContent() {
  const city = "Muçum";
  const [data, setData] = useState<{ projection: StationProjection | null; observation: CurrentMucumObservation | null; refresh: ProjectionRefreshState | null; failed: boolean; stale: boolean; loading: boolean; now: number }>({ projection: null, observation: null, refresh: null, failed: false, stale: false, loading: true, now: 0 });
  useEffect(() => {
    const controller = new AbortController();
    let pending = false;
    async function refresh() {
      if (pending) return;
      pending = true;
      try {
        const observationRequest = fetch("/api/sace-mucum", { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15_000)]) })
          .then(async response => response.ok ? readCurrentMucumObservation(await response.json()) : null)
          .catch(() => null);
        const response = await fetch("/api/projection?station=mucum", { cache: "no-store", signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15_000)]) });
        if (!response.ok) throw new Error("unavailable");
        const payload = await response.json();
        if (payload.projection && !validProjection(payload.projection, "mucum")) throw new Error("invalid forecast");
        const observation = await observationRequest;
        if (!controller.signal.aborted) {
          setData(previous => ({ projection: payload.projection ?? previous.projection, observation, refresh: readRefreshState(payload.refresh), failed: Boolean(payload.failed), stale: Boolean(payload.stale), loading: false, now: Date.now() }));
        }
      } catch {
        if (!controller.signal.aborted) setData(previous => ({ ...previous, failed: true, loading: false, now: Date.now() }));
      } finally { pending = false; }
    }
    void refresh();
    const timer = setInterval(() => void refresh(), 60_000);
    return () => { controller.abort(); clearInterval(timer); };
  }, []);
  const projection = data.projection;
  const stale = projection && (data.stale || projectionIsStale(projection, data.now));
  const hydrometric = projection?.models[0].id === HYDROMETRIC_MODEL_ID;
  const points = projection?.models[0].points.filter(point => Date.parse(point.timestamp) > data.now).slice(0, 6) ?? [];
  const newerObservation = projection && data.observation && Date.parse(data.observation.timestamp) > Date.parse(projection.referenceAt) ? data.observation : null;
  const contradicted = projection && projectionContradictedByObservation(projection, newerObservation, data.now);
  const period = forecastPeriod(points);
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
      <ProjectionRefreshNotice refresh={data.refresh} failed={data.failed} />
      {stale && !data.failed && <p className="projection-warning" role="status">Último cálculo disponível: {dateTime(projection.generatedAt)}. Os dados desta rodada podem estar desatualizados; confira os níveis do rio acima.</p>}
      {!projection ? <p className="projection-empty" role="status">{data.loading ? "Carregando previsão…" : data.failed ? "Previsão temporariamente indisponível." : "Aguardando o primeiro cálculo."}</p> : (
        <>
          {!data.observation && !data.loading && <p className="projection-warning" role="status">Não foi possível conferir a previsão com a leitura mais recente da régua de Muçum.</p>}
          {contradicted && <p className="projection-warning" role="alert">A leitura mais recente já está acima do valor previsto para {dateTime(points[0].timestamp)}. A curva desta rodada foi suspensa porque não representa a subida já medida. Consulte o cálculo original abaixo e acompanhe as medições e alertas oficiais.</p>}
          {points.length && !contradicted ? <>
            <p className="projection-details">Calculada em {dateTime(projection.generatedAt)}. Dados de {dateTime(projection.referenceAt)}. Previsão {period}.</p>
            <svg className="projection-chart" viewBox="0 0 770 205" role="img" aria-label={`Nível observado em ${city} seguido da previsão de nível ${period}, em metros. Valores disponíveis na tabela abaixo.`}>
              {[min, (min + max) / 2, max].map(v => <g key={v}><line x1="45" x2="745" y1={y(v)} y2={y(v)} stroke="currentColor" opacity=".1" /><text x="35" y={y(v) + 4} textAnchor="end">{v.toFixed(1)}</text></g>)}
              <polyline points={line} fill="none" stroke="#37836b" strokeWidth="2.5" strokeDasharray="6 4" strokeLinejoin="round" />
              <circle cx={x(chart[0].timestamp)} cy={y(chart[0].level)} r="4" fill="#37836b" />
              {points.filter((_, i) => i % 3 === 0 || i === points.length - 1).map(p => <text key={p.timestamp} x={x(p.timestamp)} y="196" textAnchor="middle">{time(p.timestamp)}</text>)}
            </svg>
            <div className="projection-table-wrap" tabIndex={0} role="region" aria-label="Previsão horária; role horizontalmente para consultar os horários"><table className="projection-table"><caption className="sr-only">Previsão do nível do rio em {city}, {period}, horário de Brasília</caption><thead><tr>{points.map(p => <th key={p.timestamp} scope="col">{time(p.timestamp)}</th>)}</tr></thead><tbody><tr>{points.map(p => <td key={p.timestamp}>{level(p.level)} <span>m</span></td>)}</tr></tbody></table></div>
          </> : contradicted ? <details className="projection-details"><summary>Ver valores da rodada anterior, sem validação pela leitura atual</summary><p>Calculada em {dateTime(projection.generatedAt)}, com dados de {dateTime(projection.referenceAt)}. Previsão original {period}.</p><div className="projection-table-wrap" tabIndex={0} role="region" aria-label="Valores da rodada anterior"><table className="projection-table"><caption className="sr-only">Valores originais da previsão de {city}, {period}, horário de Brasília</caption><thead><tr>{points.map(p => <th key={p.timestamp} scope="col">{time(p.timestamp)}</th>)}</tr></thead><tbody><tr>{points.map(p => <td key={p.timestamp}>{level(p.level)} <span>m</span></td>)}</tr></tbody></table></div></details> : <p className="projection-empty" role="status">Sem previsão atualizada para as próximas horas.</p>}
          <ProjectionExplanation hydrometric={hydrometric} />
        </>
      )}
    </div>
  );
}

function ProjectionExplanation({ hydrometric }: { hydrometric: boolean }) {
  return <details className="projection-details"><summary>Como funciona o modelo de previsão</summary>
    <p>{hydrometric
      ? "O gráfico usa o modelo hidrométrico experimental de Muçum. Ele considera níveis do rio e vazões das hidrelétricas, incluindo suas mudanças nas horas anteriores. Chuva que ainda não alterou esses níveis e vazões não entra na previsão."
      : "Esta previsão foi gerada pelo modelo anterior, que usa níveis, vazões e chuva. As próximas atualizações usam o modelo hidrométrico de Muçum."}</p>
    <p>Uma nova previsão é calculada quando os níveis e vazões necessários estão completos para a hora de referência e para o histórico usado pelo modelo. O alcance é de até 6 horas após essa referência. O gráfico mostra somente horários que ainda não passaram. Os horários são de Brasília.</p>
    <p>Este modelo é experimental: pode errar, principalmente em mudanças rápidas e situações pouco representadas no histórico. Os resultados ainda estão em validação. Não substitui alertas e orientações da Defesa Civil.</p>
  </details>;
}
