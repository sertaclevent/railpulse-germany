import { format, parseISO } from "date-fns";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartSurface } from "./ChartSurface";
import type { DailyDelayTrendPoint, WeeklyDelayTrendPoint } from "../types/dashboard";

interface DelayTrendsPanelProps {
  dailyTrends: DailyDelayTrendPoint[];
  weeklyTrends: WeeklyDelayTrendPoint[];
}

const formatDailyLabel = (value: string) => format(parseISO(value), "dd MMM");
const formatWeeklyLabel = (value: string) => {
  const weekStart = parseISO(value);
  return `W${format(weekStart, "II")}`;
};

const coerceIsoDate = (label: unknown): string | null => {
  if (typeof label !== "string" || !label) {
    return null;
  }
  return label;
};

export const DelayTrendsPanel = ({ dailyTrends, weeklyTrends }: DelayTrendsPanelProps) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
    <h2 className="font-heading text-lg font-semibold text-slate-900">Daily & Weekly Delay Trends</h2>

    <div className="mt-4 h-56">
      <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Daily Average Delay (Last 14 Days)</p>
      <ChartSurface className="h-full min-w-0">
        {({ width, height }) => (
          <LineChart width={width} height={height} data={dailyTrends}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="date" tickFormatter={formatDailyLabel} stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              labelFormatter={(label) => {
                const iso = coerceIsoDate(label);
                if (!iso) {
                  return "";
                }
                return format(parseISO(iso), "PP");
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="average_delay"
              name="Avg Delay (min)"
              stroke="#0f766e"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        )}
      </ChartSurface>
    </div>

    <div className="mt-6 h-56">
      <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Weekly Average Delay</p>
      <ChartSurface className="h-full min-w-0">
        {({ width, height }) => (
          <BarChart width={width} height={height} data={weeklyTrends}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="week_start" tickFormatter={formatWeeklyLabel} stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              labelFormatter={(label) => {
                const iso = coerceIsoDate(label);
                if (!iso) {
                  return "";
                }
                const start = parseISO(iso);
                return `Week of ${format(start, "PP")}`;
              }}
            />
            <Legend />
            <Bar dataKey="average_delay" name="Avg Delay (min)" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ChartSurface>
    </div>
  </section>
);
