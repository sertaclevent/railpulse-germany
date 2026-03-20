import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

import { ChartSurface } from "../components/ChartSurface";
import { getLineStats } from "../services/dashboardApi";
import type { LineStatsResponseData } from "../types/dashboard";
import { formatPercent } from "../utils/format";

const riskBandClass = (riskBand: "low" | "medium" | "high"): string => {
  if (riskBand === "high") {
    return "bg-rose-100 text-rose-800 border-rose-200";
  }
  if (riskBand === "medium") {
    return "bg-amber-100 text-amber-800 border-amber-200";
  }
  return "bg-emerald-100 text-emerald-800 border-emerald-200";
};

export const LineDetailPage = () => {
  const { lineName = "" } = useParams();
  const decodedLineName = useMemo(() => {
    try {
      return decodeURIComponent(lineName);
    } catch {
      return lineName;
    }
  }, [lineName]);
  const [data, setData] = useState<LineStatsResponseData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const payload = await getLineStats(decodedLineName, 30);
        if (!active) {
          return;
        }
        setData(payload);
      } catch {
        if (!active) {
          return;
        }
        setError("Line statistics could not be loaded.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void load();
    const intervalId = window.setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      void getLineStats(decodedLineName, 30)
        .then((payload) => {
          if (active) {
            setData(payload);
          }
        })
        .catch(() => {
          if (active) {
            setError("Line statistics could not be loaded.");
          }
        });
    }, 60_000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [decodedLineName]);

  if (loading) {
    return (
      <main className="mx-auto max-w-[1400px] px-4 py-6 md:px-6">
        <p className="text-sm text-slate-600">Loading line statistics...</p>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="mx-auto max-w-[1400px] px-4 py-6 md:px-6">
        <Link to="/" className="text-sm text-slate-700 underline">
          Back to dashboard
        </Link>
        <p className="mt-3 text-sm text-rose-700">{error ?? "No data available."}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-[1400px] px-4 py-6 md:px-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-300/50">
        <Link to="/" className="text-sm text-slate-700 underline">
          Back to dashboard
        </Link>
        <h1 className="mt-3 font-heading text-3xl font-semibold text-slate-900">Line: {data.line_name}</h1>
        <p className="mt-1 text-sm text-slate-600">Last {data.days} days across all collected stations.</p>

        <div className="mt-3 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide">
          <span className={`rounded-full border px-2 py-1 ${riskBandClass(data.risk_forecast.risk_band)}`}>{data.risk_forecast.risk_band} risk</span>
          <span className="text-slate-700">Delay probability: {formatPercent(data.risk_forecast.delay_probability)}</span>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Total Samples</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{data.risk_forecast.sample_size}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Delay Probability</p>
            <p className="mt-1 text-2xl font-semibold text-rose-700">{formatPercent(data.risk_forecast.delay_probability)}</p>
            <p className="mt-1 text-xs text-slate-500">
              95% CI {formatPercent(data.risk_forecast.delay_probability_confidence_95.lower)} -{" "}
              {formatPercent(data.risk_forecast.delay_probability_confidence_95.upper)}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">5+ min / 10+ min</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">
              {formatPercent(data.risk_forecast.delay_over_5_probability)} / {formatPercent(data.risk_forecast.delay_over_10_probability)}
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Expected Delay</p>
            <p className="mt-1 text-2xl font-semibold text-slate-900">{data.risk_forecast.expected_delay_minutes.toFixed(1)} min</p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <div className="h-64">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Daily Average Delay</p>
            <ChartSurface className="h-full min-w-0">
              {({ width, height }) => (
                <LineChart width={width} height={height} data={data.daily}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="average_delay" name="Avg Delay (min)" stroke="#0f766e" strokeWidth={2} dot={false} />
                </LineChart>
              )}
            </ChartSurface>
          </div>

          <div className="h-64">
            <p className="mb-2 text-xs uppercase tracking-wide text-slate-500">Weekly Average Delay</p>
            <ChartSurface className="h-full min-w-0">
              {({ width, height }) => (
                <BarChart width={width} height={height} data={data.weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="week_start" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="average_delay" name="Avg Delay (min)" fill="#1d4ed8" radius={[4, 4, 0, 0]} />
                </BarChart>
              )}
            </ChartSurface>
          </div>
        </div>
      </div>

      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
        <h2 className="font-heading text-lg font-semibold text-slate-900">Line Corridor Station Risk</h2>
        <p className="mt-1 text-sm text-slate-600">
          Her satir, bu tren kodunun ilgili istasyonda gecikme ihtimalini gosterir.
        </p>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-3 py-2">Station</th>
                <th className="px-3 py-2">City</th>
                <th className="px-3 py-2">Samples</th>
                <th className="px-3 py-2">Delay Risk</th>
                <th className="px-3 py-2">5+ / 10+</th>
                <th className="px-3 py-2">Avg Delay</th>
                <th className="px-3 py-2">95% CI</th>
              </tr>
            </thead>
            <tbody>
              {data.station_profile.map((station) => (
                <tr key={station.station_id} className="border-t border-slate-100 text-slate-700">
                  <td className="px-3 py-2 font-medium text-slate-900">{station.name}</td>
                  <td className="px-3 py-2">{station.city || "-"}</td>
                  <td className="px-3 py-2">{station.total_trains}</td>
                  <td className="px-3 py-2 font-semibold text-rose-700">{formatPercent(station.delay_probability)}</td>
                  <td className="px-3 py-2">
                    {formatPercent(station.delay_over_5_probability)} / {formatPercent(station.delay_over_10_probability)}
                  </td>
                  <td className="px-3 py-2">{station.average_delay.toFixed(1)} min</td>
                  <td className="px-3 py-2 text-xs text-slate-600">
                    {formatPercent(station.delay_probability_confidence_95.lower)} -{" "}
                    {formatPercent(station.delay_probability_confidence_95.upper)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
};
