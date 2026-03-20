import { useEffect, useRef, useState, type ReactNode } from "react";

interface ChartSurfaceProps {
  className?: string;
  children: (size: { width: number; height: number }) => ReactNode;
}

export const ChartSurface = ({ className, children }: ChartSurfaceProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    const updateSize = () => {
      const rect = container.getBoundingClientRect();
      setSize({
        width: Math.max(Math.floor(rect.width), 0),
        height: Math.max(Math.floor(rect.height), 0),
      });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(container);

    return () => {
      observer.disconnect();
    };
  }, []);

  return <div ref={containerRef} className={className}>{size.width > 0 && size.height > 0 ? children(size) : null}</div>;
};
