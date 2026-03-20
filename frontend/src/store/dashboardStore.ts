import { create } from "zustand";

import {
  getDelayTrends,
  getHourlyDelay,
  getLineCatalog,
  getLineRankings,
  getStationLineProbabilities,
  getStationBoard,
  getStationStats,
  searchStations,
  type DashboardFilters,
} from "../services/dashboardApi";
import type {
  BoardType,
  DailyDelayTrendPoint,
  DashboardStats,
  DelayDistributionPoint,
  HourlyDelayPoint,
  LineCatalogItem,
  LineRankingsResponseData,
  StationLineProbabilitiesResponseData,
  Station,
  TrainRecord,
  WeeklyDelayTrendPoint,
} from "../types/dashboard";

interface DashboardState {
  selectedStation: Station | null;
  stationOptions: Station[];
  allStations: Station[];
  boardType: BoardType;
  filters: DashboardFilters;
  trains: TrainRecord[];
  stationStats: DashboardStats | null;
  lineStats: DashboardStats | null;
  hourlyDelay: HourlyDelayPoint[];
  delayDistribution: DelayDistributionPoint[];
  dailyTrends: DailyDelayTrendPoint[];
  weeklyTrends: WeeklyDelayTrendPoint[];
  lineRankings: LineRankingsResponseData | null;
  lineOptions: LineCatalogItem[];
  stationLineProbabilities: StationLineProbabilitiesResponseData | null;
  requestedWindowHours: number;
  effectiveWindowHours: number;
  windowFallbackUsed: boolean;
  loadingStations: boolean;
  loadingDashboard: boolean;
  error: string | null;
  initializeDashboard: () => Promise<void>;
  searchStationOptions: (query: string) => Promise<void>;
  setSelectedStation: (station: Station) => Promise<void>;
  setBoardType: (boardType: BoardType) => Promise<void>;
  setWindow: (window: DashboardFilters["window"]) => Promise<void>;
  setDelayThreshold: (delayThreshold: DashboardFilters["delayThreshold"]) => Promise<void>;
  setCategoryFilter: (category: string) => Promise<void>;
  setLineFilter: (line: string) => Promise<void>;
  refreshLineRankings: () => Promise<void>;
  refreshDashboard: () => Promise<void>;
}

const defaultFilters: DashboardFilters = {
  window: "2h",
  delayThreshold: "all",
  category: "",
  line: "",
};

const parseWindowHours = (window: DashboardFilters["window"]): number => Number(window.replace("h", "")) || 2;

const pickDefaultStation = (stations: Station[]): Station | null => {
  if (stations.length === 0) {
    return null;
  }

  const munich = stations.find((station) => station.eva_number === "8000261");
  return munich ?? stations[0];
};

export const useDashboardStore = create<DashboardState>((set, get) => ({
  selectedStation: null,
  stationOptions: [],
  allStations: [],
  boardType: "departure",
  filters: defaultFilters,
  trains: [],
  stationStats: null,
  lineStats: null,
  hourlyDelay: [],
  delayDistribution: [],
  dailyTrends: [],
  weeklyTrends: [],
  lineRankings: null,
  lineOptions: [],
  stationLineProbabilities: null,
  requestedWindowHours: 2,
  effectiveWindowHours: 2,
  windowFallbackUsed: false,
  loadingStations: false,
  loadingDashboard: false,
  error: null,

  initializeDashboard: async () => {
    if (get().loadingStations) {
      return;
    }

    set({ loadingStations: true, error: null });
    try {
      const [stationsResult, lineCatalogResult] = await Promise.allSettled([searchStations("", 6000), getLineCatalog(30, 400, "")]);
      if (stationsResult.status !== "fulfilled") {
        throw new Error("Stations could not be loaded.");
      }

      const stations = stationsResult.value;
      const selected = pickDefaultStation(stations);
      const lineOptions = lineCatalogResult.status === "fulfilled" ? lineCatalogResult.value.lines : [];

      set({
        stationOptions: stations,
        allStations: stations,
        selectedStation: selected,
        lineOptions,
        loadingStations: false,
      });

      if (selected) {
        await get().refreshDashboard();
      }
    } catch {
      set({
        loadingStations: false,
        error: "Stations could not be loaded. Check API connectivity.",
      });
    }
  },

  searchStationOptions: async (query: string) => {
    set({ loadingStations: true, error: null });
    try {
      const stations = await searchStations(query, 100);
      set({ stationOptions: stations, loadingStations: false });
    } catch {
      set({
        loadingStations: false,
        error: "Station search failed. Try a different query.",
      });
    }
  },

  setSelectedStation: async (station: Station) => {
    set({ selectedStation: station, error: null });
    await get().refreshDashboard();
  },

  setBoardType: async (boardType: BoardType) => {
    set({ boardType });
    await get().refreshDashboard();
  },

  setWindow: async (window) => {
    set((state) => ({ filters: { ...state.filters, window } }));
    await get().refreshDashboard();
  },

  setDelayThreshold: async (delayThreshold) => {
    set((state) => ({ filters: { ...state.filters, delayThreshold } }));
    await get().refreshDashboard();
  },

  setCategoryFilter: async (category) => {
    set((state) => ({ filters: { ...state.filters, category } }));
  },

  setLineFilter: async (line) => {
    set((state) => ({ filters: { ...state.filters, line } }));
    await get().refreshDashboard();
  },

  refreshLineRankings: async () => {
    try {
      const rankings = await getLineRankings(14, 20);
      set({ lineRankings: rankings });
    } catch {
      set({ lineRankings: null });
    }
  },

  refreshDashboard: async () => {
    const state = get();
    if (!state.selectedStation || state.loadingDashboard) {
      return;
    }

    set({
      loadingDashboard: true,
      error: null,
      requestedWindowHours: parseWindowHours(state.filters.window),
      effectiveWindowHours: parseWindowHours(state.filters.window),
      windowFallbackUsed: false,
    });

    try {
      const stationId = state.selectedStation.id;
      const boardData = await getStationBoard(stationId, state.boardType, state.filters);
      const stationStatsFilters = { ...state.filters, line: "" };
      const lineStatsPromise = state.filters.line
        ? getStationStats(stationId, state.boardType, state.filters)
        : Promise.resolve<DashboardStats | null>(null);
      const [stationStatsResult, lineStatsResult, chartResult, trendResult, rankingsResult, stationLineProbabilitiesResult] = await Promise.allSettled([
        getStationStats(stationId, state.boardType, stationStatsFilters),
        lineStatsPromise,
        getHourlyDelay(stationId, state.boardType, state.filters.line),
        getDelayTrends(stationId, state.boardType, state.filters.line, 14),
        getLineRankings(14, 20),
        getStationLineProbabilities(stationId, state.boardType, 30, 6),
      ]);

      const current = get();
      const stationStatsData =
        stationStatsResult.status === "fulfilled" ? stationStatsResult.value : current.stationStats;
      const lineStatsData =
        lineStatsResult.status === "fulfilled" ? lineStatsResult.value : current.lineStats;
      const chartData = chartResult.status === "fulfilled" ? chartResult.value : null;
      const trendData = trendResult.status === "fulfilled" ? trendResult.value : null;
      const rankingsData = rankingsResult.status === "fulfilled" ? rankingsResult.value : current.lineRankings;
      const stationLineProbabilities =
        stationLineProbabilitiesResult.status === "fulfilled"
          ? stationLineProbabilitiesResult.value
          : current.stationLineProbabilities;
      const mergedLineOptionsMap = new Map<string, LineCatalogItem>();
      for (const item of current.lineOptions) {
        mergedLineOptionsMap.set(item.line_name, item);
      }
      for (const train of boardData.trains) {
        if (!mergedLineOptionsMap.has(train.train_line)) {
          mergedLineOptionsMap.set(train.train_line, {
            line_name: train.train_line,
            total_trains: 0,
            average_delay: train.delay_minutes,
            delay_probability: train.delay_minutes > 0 ? 1 : 0,
          });
        }
      }
      const requestedWindowHours = boardData.requested_window_hours ?? parseWindowHours(state.filters.window);
      const effectiveWindowHours = boardData.window_hours ?? requestedWindowHours;
      const windowFallbackUsed = effectiveWindowHours > requestedWindowHours;

      set({
        trains: boardData.trains,
        stationStats: stationStatsData,
        lineStats: state.filters.line ? lineStatsData : null,
        hourlyDelay: chartData ? chartData.hourly_average_delay : current.hourlyDelay,
        delayDistribution: chartData ? chartData.delay_distribution : current.delayDistribution,
        dailyTrends: trendData ? trendData.daily : current.dailyTrends,
        weeklyTrends: trendData ? trendData.weekly : current.weeklyTrends,
        lineRankings: rankingsData,
        lineOptions: Array.from(mergedLineOptionsMap.values()).sort((a, b) => a.line_name.localeCompare(b.line_name)),
        stationLineProbabilities,
        requestedWindowHours,
        effectiveWindowHours,
        windowFallbackUsed,
        loadingDashboard: false,
      });
    } catch {
      set({
        loadingDashboard: false,
        error: "Live train data could not be loaded right now.",
      });
    }
  },
}));
