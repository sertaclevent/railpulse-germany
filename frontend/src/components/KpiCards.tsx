import { formatPercent } from "../utils/format";
import type { DashboardStats } from "../types/dashboard";

interface KpiCardsProps {
  stationStats: DashboardStats | null;
  lineStats: DashboardStats | null;
  selectedLine: string;
  stationName: string;
}

interface KpiItem {
  label: string;
  value: string;
}

const buildMetrics = (stats: DashboardStats | null): KpiItem[] => [
  { label: "Total Trains", value: String(stats?.total_trains ?? 0) },
  { label: "Average Delay", value: `${stats?.average_delay ?? 0} min` },
  { label: "Median Delay", value: `${stats?.median_delay ?? 0} min` },
  { label: "On-time Ratio", value: formatPercent(stats?.on_time_ratio ?? 0) },
  { label: "Delay Probability", value: formatPercent(stats?.delayed_any_ratio ?? 0) },
  { label: "Delayed 5+ Ratio", value: formatPercent(stats?.delayed_over_5_ratio ?? 0) },
  { label: "Delayed 10+ Ratio", value: formatPercent(stats?.delayed_over_10_ratio ?? 0) },
  { label: "Maximum Delay", value: `${stats?.maximum_delay ?? 0} min` },
];

const MetricGrid = ({ metrics }: { metrics: KpiItem[] }) => (
  <div className="mt-3 grid grid-cols-2 gap-3">
    {metrics.map((metric) => (
      <article key={metric.label} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3">
        <p className="text-xs uppercase tracking-wide text-slate-500">{metric.label}</p>
        <p className="mt-1 font-heading text-xl font-semibold text-slate-900">{metric.value}</p>
      </article>
    ))}
  </div>
);

export const KpiCards = ({ stationStats, lineStats, selectedLine, stationName }: KpiCardsProps) => {
  const stationMetrics = buildMetrics(stationStats);
  const lineMetrics = buildMetrics(lineStats);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
      <h2 className="font-heading text-lg font-semibold text-slate-900">KPI Summary</h2>
      <p className="mt-1 text-xs text-slate-500">Station-based ({stationName || "Selected station"})</p>
      <MetricGrid metrics={stationMetrics} />

      {selectedLine ? (
        <>
          <p className="mt-5 text-xs text-slate-500">Train-based (Line: {selectedLine})</p>
          <MetricGrid metrics={lineMetrics} />
        </>
      ) : (
        <p className="mt-4 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-600">
          Train-based KPI icin "Train Line Code" seciniz.
        </p>
      )}
    </section>
  );
};
