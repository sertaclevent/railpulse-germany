export type BoardType = "departure" | "arrival";

export type TimeWindow = "1h" | "2h" | "4h" | "6h";

export type DelayThreshold = "all" | "5" | "10";

export interface Station {
  id: number;
  eva_number: string;
  name: string;
  city: string;
  latitude: number | null;
  longitude: number | null;
  label: string;
  state?: string;
  country?: string;
  ds100?: string;
  short_description?: string;
}

export interface TrainRecord {
  id: number;
  station: number;
  board_type: BoardType;
  train_line: string;
  category: string;
  destination_or_origin: string;
  planned_time: string;
  updated_time: string | null;
  planned_time_local: string;
  updated_time_local: string | null;
  delay_minutes: number;
  platform: string;
  status: string;
}

export interface DashboardStats {
  station_id: number;
  board_type: BoardType;
  window_hours: number;
  requested_window_hours?: number;
  total_trains: number;
  average_delay: number;
  median_delay: number;
  on_time_ratio: number;
  delayed_any_ratio: number;
  delayed_over_5_ratio: number;
  delayed_over_10_ratio: number;
  maximum_delay: number;
}

export interface HourlyDelayPoint {
  hour: number;
  average_delay: number;
  trains: number;
}

export interface DelayDistributionPoint {
  bucket: string;
  count: number;
}

export interface DailyDelayTrendPoint {
  date: string;
  total_trains: number;
  average_delay: number;
  median_delay: number;
  on_time_ratio: number;
  delayed_over_5_ratio: number;
  maximum_delay: number;
}

export interface WeeklyDelayTrendPoint {
  week_start: string;
  week_end: string;
  total_trains: number;
  average_delay: number;
  median_delay: number;
  on_time_ratio: number;
  delayed_over_5_ratio: number;
  maximum_delay: number;
}

export interface DelayTrendResponseData {
  station_id: number;
  board_type: BoardType;
  days: number;
  daily: DailyDelayTrendPoint[];
  weekly: WeeklyDelayTrendPoint[];
}

export interface LineRankingItem {
  line_name: string;
  total_trains: number;
  average_delay: number;
  maximum_delay: number;
  on_time_ratio: number;
  delayed_any_ratio: number;
  delayed_over_5_ratio: number;
  delayed_over_10_ratio: number;
  stations_covered: number;
  risk_band: "low" | "medium" | "high";
}

export interface LineCatalogItem {
  line_name: string;
  total_trains: number;
  average_delay: number;
  delay_probability: number;
}

export interface LineCatalogResponseData {
  days: number;
  limit: number;
  query: string;
  lines: LineCatalogItem[];
}

export interface LineRankingsResponseData {
  days: number;
  min_trains: number;
  top_n: number;
  most_punctual: LineRankingItem[];
  most_delayed: LineRankingItem[];
}

export interface LineStationStats {
  station_id: number;
  name: string;
  city: string;
  total_trains: number;
  average_delay: number;
  maximum_delay: number;
  on_time_ratio: number;
  delay_probability: number;
  delay_over_5_probability: number;
  delay_over_10_probability: number;
  delay_probability_confidence_95: {
    lower: number;
    upper: number;
  };
}

export interface RiskForecast {
  sample_size: number;
  delay_probability: number;
  on_time_probability: number;
  delay_over_5_probability: number;
  delay_over_10_probability: number;
  expected_delay_minutes: number;
  delay_probability_confidence_95: {
    lower: number;
    upper: number;
  };
  risk_band: "low" | "medium" | "high";
}

export interface LineStatsResponseData {
  line_name: string;
  days: number;
  summary: {
    total_trains: number;
    average_delay: number;
    median_delay: number;
    on_time_ratio: number;
    delayed_over_5_ratio: number;
    delayed_over_10_ratio: number;
    maximum_delay: number;
  };
  risk_forecast: RiskForecast;
  daily: DailyDelayTrendPoint[];
  weekly: WeeklyDelayTrendPoint[];
  top_stations: LineStationStats[];
  station_profile: LineStationStats[];
  most_risky_stations: LineStationStats[];
}

export interface StationLineProbabilityItem {
  line_name: string;
  category: string;
  total_trains: number;
  average_delay: number;
  maximum_delay: number;
  on_time_probability: number;
  delay_probability: number;
  delay_over_5_probability: number;
  delay_over_10_probability: number;
  delay_probability_confidence_95: {
    lower: number;
    upper: number;
  };
  risk_band: "low" | "medium" | "high";
}

export interface StationLineProbabilitiesResponseData {
  station_id: number;
  board_type: BoardType;
  days: number;
  min_trains: number;
  top_n: number;
  sampled_lines: number;
  most_risky: StationLineProbabilityItem[];
  most_reliable: StationLineProbabilityItem[];
}

export interface BoardResponseData {
  station: Station;
  board_type: BoardType;
  window_hours: number;
  requested_window_hours?: number;
  filters: {
    delay_threshold: number;
    category: string;
    line: string;
  };
  trains: TrainRecord[];
}
