import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

import { useDebounce } from "../hooks/useDebounce";
import type { Station } from "../types/dashboard";

interface StationSearchProps {
  stations: Station[];
  selectedStation: Station | null;
  loading: boolean;
  onSearch: (query: string) => void;
  onSelect: (station: Station) => void;
  compact?: boolean;
}

export const StationSearch = ({
  stations,
  selectedStation,
  loading,
  onSearch,
  onSelect,
  compact = false,
}: StationSearchProps) => {
  const [query, setQuery] = useState(selectedStation?.label ?? "");
  const [open, setOpen] = useState(false);
  const [hasUserTyped, setHasUserTyped] = useState(false);
  const debouncedQuery = useDebounce(query, 350);

  useEffect(() => {
    setQuery(selectedStation?.label ?? "");
    setHasUserTyped(false);
  }, [selectedStation?.id, selectedStation?.label]);

  useEffect(() => {
    if (!open || !hasUserTyped) {
      return;
    }

    const trimmed = debouncedQuery.trim();
    if (trimmed.length < 2) {
      return;
    }

    onSearch(trimmed);
  }, [debouncedQuery, hasUserTyped, onSearch, open]);

  const options = useMemo(() => stations.slice(0, 8), [stations]);

  return (
    <div className="relative">
      <label className={clsx("mb-1 block text-xs font-medium uppercase tracking-wide", compact ? "text-slate-500" : "text-cyan-100")}>
        Station Search
      </label>
      <input
        value={query}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          window.setTimeout(() => setOpen(false), 120);
        }}
        onChange={(event) => {
          setHasUserTyped(true);
          setQuery(event.target.value);
        }}
        placeholder="Search station name"
        className={clsx(
          "w-full rounded-xl border px-3 py-2 text-sm outline-none transition",
          compact
            ? "border-slate-300 bg-white text-slate-900 focus:border-cyan-600"
            : "border-cyan-500/40 bg-slate-900/40 text-white placeholder:text-cyan-100/60 focus:border-cyan-300",
        )}
      />
      {open && (
        <div className="absolute z-[1200] mt-2 max-h-64 w-full overflow-auto rounded-xl border border-slate-200 bg-white shadow-xl shadow-slate-300/40">
          {loading && <p className="px-3 py-2 text-sm text-slate-500">Searching stations...</p>}
          {!loading && options.length === 0 && <p className="px-3 py-2 text-sm text-slate-500">No matching station.</p>}
          {!loading &&
            options.map((station) => (
              <button
                key={station.id}
                type="button"
                onMouseDown={() => {
                  setQuery(station.label);
                  setHasUserTyped(false);
                  onSelect(station);
                }}
                className="block w-full border-b border-slate-100 px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
              >
                <span className="font-medium text-slate-900">{station.name}</span>
                <span className="ml-2 text-xs text-slate-500">{station.city}</span>
              </button>
            ))}
        </div>
      )}
    </div>
  );
};
