import { render, screen } from "@testing-library/react";

import { KpiCards } from "./KpiCards";

describe("KpiCards", () => {
  it("renders KPI values", () => {
    render(
      <KpiCards
        stationStats={{
          station_id: 1,
          board_type: "departure",
          window_hours: 2,
          total_trains: 16,
          average_delay: 5.4,
          median_delay: 4,
          on_time_ratio: 0.31,
          delayed_any_ratio: 0.69,
          delayed_over_5_ratio: 0.44,
          delayed_over_10_ratio: 0.2,
          maximum_delay: 19,
        }}
        lineStats={{
          station_id: 1,
          board_type: "departure",
          window_hours: 2,
          total_trains: 5,
          average_delay: 8.2,
          median_delay: 7,
          on_time_ratio: 0.2,
          delayed_any_ratio: 0.8,
          delayed_over_5_ratio: 0.6,
          delayed_over_10_ratio: 0.4,
          maximum_delay: 24,
        }}
        selectedLine="ICE 100"
        stationName="Berlin Hbf"
      />,
    );

    expect(screen.getByText("KPI Summary")).toBeInTheDocument();
    expect(screen.getByText("Station-based (Berlin Hbf)")).toBeInTheDocument();
    expect(screen.getByText("Train-based (Line: ICE 100)")).toBeInTheDocument();
    expect(screen.getByText("16")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("5.4 min")).toBeInTheDocument();
    expect(screen.getByText("8.2 min")).toBeInTheDocument();
    expect(screen.getByText("31%")).toBeInTheDocument();
  });
});
