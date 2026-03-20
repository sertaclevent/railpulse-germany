import { Link } from "react-router-dom";

import type { StationLineProbabilitiesResponseData } from "../types/dashboard";
import { formatPercent } from "../utils/format";

interface StationLineRiskPanelProps {
  data: StationLineProbabilitiesResponseData | null;
}

const RiskTable = ({
  title,
  rows,
  accentClassName,
}: {
  title: string;
  rows: StationLineProbabilitiesResponseData["most_risky"];
  accentClassName: string;
}) => (
  <div>
    <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-600">{title}</h3>
    <div className="mt-2 overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full border-collapse text-sm">
        <thead>
          <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-3 py-2">Line</th>
            <th className="px-3 py-2">Delay Risk</th>
            <th className="px-3 py-2">95% CI</th>
            <th className="px-3 py-2">Avg Delay</th>
            <th className="px-3 py-2">Samples</th>
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
              <td className={`px-3 py-2 font-semibold ${accentClassName}`}>{formatPercent(line.delay_probability)}</td>
              <td className="px-3 py-2 text-xs text-slate-600">
                {formatPercent(line.delay_probability_confidence_95.lower)} - {formatPercent(line.delay_probability_confidence_95.upper)}
              </td>
              <td className="px-3 py-2">{line.average_delay.toFixed(1)} min</td>
              <td className="px-3 py-2">{line.total_trains}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

export const StationLineRiskPanel = ({ data }: StationLineRiskPanelProps) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
      <h2 className="font-heading text-lg font-semibold text-slate-900">Station Train-Code Delay Probability</h2>
      <p className="text-xs uppercase tracking-wide text-slate-500">
        Last {data?.days ?? 30} days, min {data?.min_trains ?? 6} samples
      </p>
    </div>

    {!data || (data.most_risky.length === 0 && data.most_reliable.length === 0) ? (
      <p className="text-sm text-slate-600">Risk probabilities will appear once enough samples are collected for this station.</p>
    ) : (
      <div className="grid gap-4 lg:grid-cols-2">
        <RiskTable title="Most Risky Codes" rows={data.most_risky} accentClassName="text-rose-700" />
        <RiskTable title="Most Reliable Codes" rows={data.most_reliable} accentClassName="text-emerald-700" />
      </div>
    )}
  </section>
);
