export const formatDelayLabel = (delay: number): string => {
  if (delay <= 0) {
    return "On time";
  }
  return `${delay} min`;
};

export const formatPercent = (value: number): string => `${Math.round(value * 100)}%`;

export const formatLocalTime = (isoString: string | null): string => {
  if (!isoString) {
    return "-";
  }

  const parsed = new Date(isoString);
  if (Number.isNaN(parsed.getTime())) {
    return "-";
  }

  return parsed.toLocaleTimeString("de-DE", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

export const formatHourLabel = (hour: number): string => `${hour.toString().padStart(2, "0")}:00`;
