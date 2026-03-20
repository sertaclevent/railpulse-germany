import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartSurface } from "./ChartSurface";
import type { DelayDistributionPoint, HourlyDelayPoint } from "../types/dashboard";
import { formatHourLabel } from "../utils/format";

interface DelayChartProps {
  hourlyDelay: HourlyDelayPoint[];
  delayDistribution: DelayDistributionPoint[];
}

export const DelayChart = ({ hourlyDelay, delayDistribution }: DelayChartProps) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
    <h2 className="font-heading text-lg font-semibold text-slate-900">Delay Charts</h2>

    <div className="mt-4 h-56">
      <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Hourly Average Delay</p>
      <ChartSurface className="h-full min-w-0">
        {({ width, height }) => (
          <BarChart width={width} height={height} data={hourlyDelay}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="hour" tickFormatter={(hour: number) => formatHourLabel(hour)} stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip />
            <Legend />
            <Bar dataKey="average_delay" name="Avg Delay (min)" fill="#0f766e" radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ChartSurface>
    </div>

    <div className="mt-6 h-56">
      <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Delay Distribution</p>
      <ChartSurface className="h-full min-w-0">
        {({ width, height }) => (
          <BarChart width={width} height={height} data={delayDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="bucket" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" name="Trains" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
          </BarChart>
        )}
      </ChartSurface>
    </div>
  </section>
);
