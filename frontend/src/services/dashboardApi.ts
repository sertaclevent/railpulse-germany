import { httpClient } from "./http";
import type {
  BoardResponseData,
  BoardType,
  DelayTrendResponseData,
  DashboardStats,
  DelayDistributionPoint,
  HourlyDelayPoint,
  LineCatalogResponseData,
  LineRankingsResponseData,
  LineStatsResponseData,
  StationLineProbabilitiesResponseData,
  Station,
} from "../types/dashboard";

interface ApiEnvelope<T> {
  success: boolean;
  data: T;
}

interface HourlyResponseData {
  station_id: number;
  board_type: BoardType;
  hourly_average_delay: HourlyDelayPoint[];
  delay_distribution: DelayDistributionPoint[];
}

export interface DashboardFilters {
  window: "1h" | "2h" | "4h" | "6h";
  delayThreshold: "all" | "5" | "10";
  category: string;
  line: string;
}

const useFrontendFallback = import.meta.env.VITE_USE_SAMPLE_DATA === "true";

const fetchFallbackJson = async <T>(name: string): Promise<T> => {
  const response = await fetch(`${import.meta.env.BASE_URL}fallback/${name}`);
  if (!response.ok) {
    throw new Error("Fallback sample data could not be loaded.");
  }
  return (await response.json()) as T;
};

export const searchStations = async (query: string, limit = 12): Promise<Station[]> => {
  try {
    const response = await httpClient.get<ApiEnvelope<Station[]>>("/stations/search", {
      params: { q: query, limit },
    });
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Station search failed.");
    }
    return fetchFallbackJson<Station[]>("stations.json");
  }
};

export const getStationBoard = async (
  stationId: number,
  boardType: BoardType,
  filters: DashboardFilters,
): Promise<BoardResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<BoardResponseData>>(
      `/stations/${stationId}/board`,
      {
        params: {
          type: boardType,
          window: filters.window,
          delay_threshold: filters.delayThreshold,
          category: filters.category,
          line: filters.line,
        },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Board data failed.");
    }
    return fetchFallbackJson<BoardResponseData>("board.json");
  }
};

export const getStationStats = async (
  stationId: number,
  boardType: BoardType,
  filters: DashboardFilters,
): Promise<DashboardStats> => {
  try {
    const response = await httpClient.get<ApiEnvelope<DashboardStats>>(
      `/stations/${stationId}/stats`,
      {
        params: {
          type: boardType,
          window: filters.window,
          delay_threshold: filters.delayThreshold,
          category: filters.category,
          line: filters.line,
        },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Stats data failed.");
    }
    return fetchFallbackJson<DashboardStats>("stats.json");
  }
};

export const getHourlyDelay = async (
  stationId: number,
  boardType: BoardType,
  line = "",
): Promise<HourlyResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<HourlyResponseData>>(
      `/stations/${stationId}/hourly-delay`,
      {
        params: {
          type: boardType,
          line,
        },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Hourly delay data failed.");
    }
    return fetchFallbackJson<HourlyResponseData>("hourly-delay.json");
  }
};

export const getDelayTrends = async (
  stationId: number,
  boardType: BoardType,
  line = "",
  days = 14,
): Promise<DelayTrendResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<DelayTrendResponseData>>(
      `/stations/${stationId}/delay-trends`,
      {
        params: {
          type: boardType,
          line,
          days,
        },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Delay trend data failed.");
    }
    return fetchFallbackJson<DelayTrendResponseData>("delay-trends.json");
  }
};

export const getLineRankings = async (
  days = 14,
  minTrains = 20,
): Promise<LineRankingsResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<LineRankingsResponseData>>("/lines/rankings", {
      params: {
        days,
        min_trains: minTrains,
        top_n: 5,
      },
    });
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Line rankings failed.");
    }
    return fetchFallbackJson<LineRankingsResponseData>("line-rankings.json");
  }
};

export const getLineCatalog = async (
  days = 30,
  limit = 200,
  query = "",
): Promise<LineCatalogResponseData> => {
  const response = await httpClient.get<ApiEnvelope<LineCatalogResponseData>>("/lines/catalog", {
    params: { days, limit, q: query },
  });
  return response.data.data;
};

export const getLineStats = async (
  lineName: string,
  days = 30,
): Promise<LineStatsResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<LineStatsResponseData>>(
      `/lines/${encodeURIComponent(lineName)}/stats`,
      {
        params: { days, top_stations: 50 },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Line stats failed.");
    }
    return fetchFallbackJson<LineStatsResponseData>("line-stats.json");
  }
};

export const getStationLineProbabilities = async (
  stationId: number,
  boardType: BoardType,
  days = 30,
  minTrains = 6,
): Promise<StationLineProbabilitiesResponseData> => {
  try {
    const response = await httpClient.get<ApiEnvelope<StationLineProbabilitiesResponseData>>(
      `/stations/${stationId}/line-probabilities`,
      {
        params: {
          type: boardType,
          days,
          min_trains: minTrains,
          top_n: 8,
        },
      },
    );
    return response.data.data;
  } catch {
    if (!useFrontendFallback) {
      throw new Error("Station line probability data failed.");
    }
    return fetchFallbackJson<StationLineProbabilitiesResponseData>("line-station-probabilities.json");
  }
};
