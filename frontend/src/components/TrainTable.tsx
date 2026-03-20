import clsx from "clsx";
import { Link } from "react-router-dom";

import type { TrainRecord } from "../types/dashboard";
import { formatDelayLabel, formatLocalTime } from "../utils/format";

interface TrainTableProps {
  trains: TrainRecord[];
}

const delayBadgeClass = (delay: number): string =>
  clsx(
    "inline-flex min-w-16 items-center justify-center rounded-full px-2 py-1 text-xs font-semibold",
    delay >= 10
      ? "bg-rose-100 text-rose-700"
      : delay >= 5
        ? "bg-amber-100 text-amber-700"
        : "bg-emerald-100 text-emerald-700",
  );

export const TrainTable = ({ trains }: TrainTableProps) => (
  <section className="rounded-2xl border border-slate-200 bg-white shadow-sm shadow-slate-300/50">
    <div className="border-b border-slate-200 px-4 py-3">
      <h2 className="font-heading text-lg font-semibold text-slate-900">Train Board</h2>
    </div>
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-3 py-3">Train Line</th>
            <th className="px-3 py-3">Destination / Origin</th>
            <th className="px-3 py-3">Planned</th>
            <th className="px-3 py-3">Updated</th>
            <th className="px-3 py-3">Delay</th>
            <th className="px-3 py-3">Platform</th>
            <th className="px-3 py-3">Status</th>
          </tr>
        </thead>
        <tbody>
          {trains.map((train) => (
            <tr key={train.id} className="border-t border-slate-100 text-sm text-slate-700">
              <td className="px-3 py-3 font-medium text-slate-900">
                <Link className="underline decoration-slate-300 hover:decoration-slate-700" to={`/lines/${encodeURIComponent(train.train_line)}`}>
                  {train.train_line}
                </Link>
              </td>
              <td className="px-3 py-3">{train.destination_or_origin}</td>
              <td className="px-3 py-3">{formatLocalTime(train.planned_time_local)}</td>
              <td className="px-3 py-3">{formatLocalTime(train.updated_time_local)}</td>
              <td className="px-3 py-3">
                <span className={delayBadgeClass(train.delay_minutes)}>{formatDelayLabel(train.delay_minutes)}</span>
              </td>
              <td className="px-3 py-3">{train.platform || "-"}</td>
              <td className="px-3 py-3">
                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs uppercase text-slate-600">{train.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </section>
);
