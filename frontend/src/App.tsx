import { useCallback, useEffect, useRef } from "react";

import { DelayChart } from "./components/DelayChart";
import { DelayTrendsPanel } from "./components/DelayTrendsPanel";
import { EmptyState } from "./components/EmptyState";
import { ErrorState } from "./components/ErrorState";
import { FilterPanel } from "./components/FilterPanel";
import { KpiCards } from "./components/KpiCards";
import { LineRankingsPanel } from "./components/LineRankingsPanel";
import { LoadingState } from "./components/LoadingState";
import { MapPanel } from "./components/MapPanel";
import { Navbar } from "./components/Navbar";
import { StationLineRiskPanel } from "./components/StationLineRiskPanel";
import { StationSearch } from "./components/StationSearch";
import { TrainTable } from "./components/TrainTable";
import { useDashboardStore } from "./store/dashboardStore";
import type { BoardType, DelayThreshold, Station, TimeWindow } from "./types/dashboard";

function App() {
  const categoryDebounceRef = useRef<number | null>(null);
  const categoryInitRef = useRef(false);

  const {
    selectedStation,
    stationOptions,
    allStations,
    boardType,
    filters,
    lineOptions,
    trains,
    stationStats,
    lineStats,
    hourlyDelay,
    delayDistribution,
    dailyTrends,
    weeklyTrends,
    lineRankings,
    stationLineProbabilities,
    requestedWindowHours,
    effectiveWindowHours,
    windowFallbackUsed,
    loadingStations,
    loadingDashboard,
    error,
    initializeDashboard,
    refreshDashboard,
    searchStationOptions,
    setSelectedStation,
    setBoardType,
    setWindow,
    setDelayThreshold,
    setCategoryFilter,
    setLineFilter,
  } = useDashboardStore();

  useEffect(() => {
    void initializeDashboard();
  }, [initializeDashboard]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      if (document.visibilityState !== "visible") {
        return;
      }
      void refreshDashboard();
    }, 60_000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [refreshDashboard]);

  useEffect(() => {
    if (!categoryInitRef.current) {
      categoryInitRef.current = true;
      return;
    }

    if (categoryDebounceRef.current) {
      window.clearTimeout(categoryDebounceRef.current);
    }

    categoryDebounceRef.current = window.setTimeout(() => {
      void refreshDashboard();
    }, 500);

    return () => {
      if (categoryDebounceRef.current) {
        window.clearTimeout(categoryDebounceRef.current);
      }
    };
  }, [filters.category, refreshDashboard]);

  const handleStationSearch = useCallback(
    (query: string) => {
      void searchStationOptions(query);
    },
    [searchStationOptions],
  );

  const handleStationSelect = useCallback(
    (station: Station) => {
      void setSelectedStation(station);
    },
    [setSelectedStation],
  );

  const stationSearch = (
    <StationSearch
      key={`top-${selectedStation?.id ?? "none"}`}
      stations={stationOptions}
      selectedStation={selectedStation}
      loading={loadingStations}
      onSearch={handleStationSearch}
      onSelect={handleStationSelect}
    />
  );

  const renderTableSection = () => {
    if (loadingDashboard) {
      return <LoadingState />;
    }

    if (error) {
      return <ErrorState message={error} />;
    }

    if (trains.length === 0) {
      return <EmptyState message="No trains match the selected filters." />;
    }

    return <TrainTable trains={trains} />;
  };

  return (
    <main className="mx-auto max-w-[1500px] px-4 py-5 md:px-6">
      <Navbar>{stationSearch}</Navbar>
      <section className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <p className="font-semibold">Lisans Aciklamasi (CC BY 4.0)</p>
        <p className="mt-1">
          Bu veri seti Creative Commons Attribution 4.0 International lisansi kapsamindadir. Deutsche Bahn verileri
          OpenStreetMap veritabanina dahil edilirse, katki listesinde Deutsche Bahn AG belirtilmesi yeterlidir.
        </p>
        <p className="mt-1">
          Veritabani lisans sahipleri tarafindan yapilan kullanimlarda her kullanimda DB atfi zorunlu degildir; dolayli
          atif (yayincinin DB&apos;ye atif yapmasi) yeterlidir.
        </p>
      </section>

      {windowFallbackUsed && !error ? (
        <section className="mt-3 rounded-2xl border border-cyan-200 bg-cyan-50 px-4 py-3 text-sm text-cyan-900">
          <p>
            No trains matched the selected {requestedWindowHours}h window for this station/filter.
            Showing next {effectiveWindowHours}h window automatically.
          </p>
        </section>
      ) : null}

      <div className="mt-5 grid gap-4 lg:grid-cols-12">
        <div className="order-2 lg:order-1 lg:col-span-3">
          <FilterPanel
            boardType={boardType}
            window={filters.window}
            delayThreshold={filters.delayThreshold}
            category={filters.category}
            selectedStation={selectedStation}
            stationOptions={allStations}
            selectedLine={filters.line}
            lineOptions={lineOptions}
            onStationChange={(station: Station) => {
              void setSelectedStation(station);
            }}
            onBoardTypeChange={(type: BoardType) => {
              void setBoardType(type);
            }}
            onWindowChange={(window: TimeWindow) => {
              void setWindow(window);
            }}
            onDelayThresholdChange={(delay: DelayThreshold) => {
              void setDelayThreshold(delay);
            }}
            onCategoryChange={(category: string) => {
              void setCategoryFilter(category);
            }}
            onLineChange={(line: string) => {
              void setLineFilter(line);
            }}
            stationSearchSlot={null}
          />
        </div>

        <div className="order-1 lg:order-2 lg:col-span-6">
          <MapPanel station={selectedStation} />
        </div>

        <div className="order-3 lg:col-span-3">
          <KpiCards
            stationStats={stationStats}
            lineStats={lineStats}
            selectedLine={filters.line}
            stationName={selectedStation?.name ?? ""}
          />
        </div>

        <div className="order-4 lg:col-span-8">{renderTableSection()}</div>

        <div className="order-5 lg:col-span-4">
          {error ? (
            <ErrorState message={error} />
          ) : hourlyDelay.length === 0 && delayDistribution.length === 0 ? (
            <EmptyState message="Delay charts will appear when train data is available." />
          ) : (
            <DelayChart hourlyDelay={hourlyDelay} delayDistribution={delayDistribution} />
          )}
        </div>

        <div className="order-6 lg:col-span-12">
          {error ? (
            <ErrorState message={error} />
          ) : (
            <DelayTrendsPanel dailyTrends={dailyTrends} weeklyTrends={weeklyTrends} />
          )}
        </div>

        <div className="order-7 lg:col-span-12">
          <LineRankingsPanel rankings={lineRankings} />
        </div>

        <div className="order-8 lg:col-span-12">
          <StationLineRiskPanel data={stationLineProbabilities} />
        </div>
      </div>
    </main>
  );
}

export default App;
