import type { ChangeEvent, ReactNode } from "react";

import type { BoardType, DelayThreshold, Station, TimeWindow } from "../types/dashboard";
import type { LineCatalogItem } from "../types/dashboard";

interface FilterPanelProps {
  boardType: BoardType;
  window: TimeWindow;
  delayThreshold: DelayThreshold;
  category: string;
  selectedStation: Station | null;
  stationOptions: Station[];
  selectedLine: string;
  lineOptions: LineCatalogItem[];
  onStationChange: (station: Station) => void;
  onBoardTypeChange: (boardType: BoardType) => void;
  onWindowChange: (window: TimeWindow) => void;
  onDelayThresholdChange: (delay: DelayThreshold) => void;
  onCategoryChange: (category: string) => void;
  onLineChange: (line: string) => void;
  stationSearchSlot: ReactNode | null;
}

export const FilterPanel = ({
  boardType,
  window,
  delayThreshold,
  category,
  selectedStation,
  stationOptions,
  selectedLine,
  lineOptions,
  onStationChange,
  onBoardTypeChange,
  onWindowChange,
  onDelayThresholdChange,
  onCategoryChange,
  onLineChange,
  stationSearchSlot,
}: FilterPanelProps) => {
  const onCategoryInput = (event: ChangeEvent<HTMLInputElement>) => {
    onCategoryChange(event.target.value);
  };

  return (
    <aside className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-300/50">
      <h2 className="font-heading text-lg font-semibold text-slate-900">Filters</h2>
      <div className="mt-4 space-y-5">
        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Station (All)</label>
          <select
            value={selectedStation?.id ?? ""}
            onChange={(event) => {
              const stationId = Number(event.target.value);
              const station = stationOptions.find((item) => item.id === stationId);
              if (station) {
                onStationChange(station);
              }
            }}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            {stationOptions.map((station) => (
              <option key={station.id} value={station.id}>
                {station.name} {station.city ? `- ${station.city}` : ""} ({station.eva_number})
              </option>
            ))}
          </select>
        </div>

        {stationSearchSlot ? <div>{stationSearchSlot}</div> : null}

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Board Type</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => onBoardTypeChange("departure")}
              className={`rounded-lg border px-3 py-2 text-sm ${
                boardType === "departure"
                  ? "border-cyan-700 bg-cyan-700 text-white"
                  : "border-slate-300 text-slate-700"
              }`}
            >
              Departure
            </button>
            <button
              type="button"
              onClick={() => onBoardTypeChange("arrival")}
              className={`rounded-lg border px-3 py-2 text-sm ${
                boardType === "arrival"
                  ? "border-cyan-700 bg-cyan-700 text-white"
                  : "border-slate-300 text-slate-700"
              }`}
            >
              Arrival
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Time Window</label>
          <select
            value={window}
            onChange={(event) => onWindowChange(event.target.value as TimeWindow)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            <option value="1h">Current hour</option>
            <option value="2h">Next 2 hours</option>
            <option value="4h">Next 4 hours</option>
            <option value="6h">Next 6 hours</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Delay Threshold</label>
          <select
            value={delayThreshold}
            onChange={(event) => onDelayThresholdChange(event.target.value as DelayThreshold)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            <option value="all">All delays</option>
            <option value="5">5+ min</option>
            <option value="10">10+ min</option>
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Train Line Code</label>
          <select
            value={selectedLine}
            onChange={(event) => onLineChange(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800"
          >
            <option value="">All lines</option>
            {lineOptions.map((line) => (
              <option key={line.line_name} value={line.line_name}>
                {line.line_name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">Train Category</label>
          <input
            value={category}
            onChange={onCategoryInput}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
            placeholder="ICE, RE, IC..."
          />
        </div>
      </div>
    </aside>
  );
};
