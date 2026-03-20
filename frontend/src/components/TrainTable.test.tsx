import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { TrainTable } from "./TrainTable";

describe("TrainTable", () => {
  it("shows train rows and delay badge", () => {
    render(
      <MemoryRouter>
        <TrainTable
          trains={[
            {
              id: 1,
              station: 1,
              board_type: "departure",
              train_line: "ICE 101",
              category: "ICE",
              destination_or_origin: "Berlin Hbf",
              planned_time: "2026-03-20T12:00:00+01:00",
              updated_time: "2026-03-20T12:09:00+01:00",
              planned_time_local: "2026-03-20T12:00:00+01:00",
              updated_time_local: "2026-03-20T12:09:00+01:00",
              delay_minutes: 9,
              platform: "12",
              status: "delayed",
            },
          ]}
        />
      </MemoryRouter>,
    );

    expect(screen.getByText("Train Board")).toBeInTheDocument();
    expect(screen.getByText("ICE 101")).toBeInTheDocument();
    expect(screen.getByText("9 min")).toBeInTheDocument();
    expect(screen.getByText("Berlin Hbf")).toBeInTheDocument();
  });
});
