import { Link } from "react-router-dom";

import type { LineRankingsResponseData } from "../types/dashboard";
import { formatPercent } from "../utils/format";

interface LineRankingsPanelProps {
  rankings: LineRankingsResponseData | null;
}

const RankingTable = ({
  title,
  rows,
  delayClassName,
}: {
  title: string;
  rows: LineRankingsResponseData["most_punctual"];
  delayClassName: string;
}) => (
  <div>
    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</h3>
    <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-3 py-2">Line</th>
            <th className="px-3 py-2">Avg Delay</th>
            <th className="px-3 py-2">Delay Risk</th>
            <th className="px-3 py-2">On Time</th>
            <th className="px-3 py-2">Trains</th>
            <th className="px-3 py-2">Stations</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((line) => (
            <tr key={line.line_name} className="border-t border-slate-100 text-slate-700">
              <td className="px-3 py-2 font-medium text-slate-900">
                <Link className="underline decoration-slate-300 hover:decoration-slate-700" to={`/lines/${encodeURIComponent(line.line_name)}`}>
                  {line.line_name}
                </Link>
              </td>
              <td className={`px-3 py-2 font-semibold ${delayClassName}`}>{line.average_delay.toFixed(1)} min</td>
              <td className={`px-3 py-2 font-semibold ${delayClassName}`}>{formatPercent(line.delayed_any_ratio)}</td>
              <td className="px-3 py-2">{formatPercent(line.on_time_ratio)}</td>
              <td className="px-3 py-2">{line.total_trains}</td>
              <td className="px-3 py-2">{line.stations_covered}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

export const LineRankingsPanel = ({ rankings }: LineRankingsPanelProps) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h2 className="font-heading text-lg font-semibold text-slate-900">Germany Line Rankings</h2>
      <p className="text-xs uppercase tracking-wide text-slate-500">
        Last {rankings?.days ?? 14} days, min {rankings?.min_trains ?? 20} trains
      </p>
    </div>

    {!rankings || (rankings.most_punctual.length === 0 && rankings.most_delayed.length === 0) ? (
      <p className="text-sm text-slate-600">Line rankings will appear after enough snapshot data is collected.</p>
    ) : (
      <div className="grid gap-4 lg:grid-cols-2">
        <RankingTable title="Top 5 Most Punctual" rows={rankings.most_punctual} delayClassName="text-emerald-700" />
        <RankingTable title="Top 5 Most Delayed" rows={rankings.most_delayed} delayClassName="text-rose-700" />
      </div>
    )}
  </section>
);
