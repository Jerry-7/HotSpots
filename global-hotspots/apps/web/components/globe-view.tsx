"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";

const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

type GlobePoint = {
  event_id: number;
  title: string;
  lat: number;
  lng: number;
  hot_score: number;
  importance_score: number;
  level: string;
};

export function GlobeView({ points }: { points: GlobePoint[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const globeRef = useRef<any>(null);
  const [dimensions, setDimensions] = useState({ width: 900, height: 520 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => {
      const width = Math.max(320, Math.floor(container.clientWidth));
      const height = Math.max(360, Math.floor(container.clientHeight));
      setDimensions({ width, height });
    });
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const centeredPoints = useMemo(() => points, [points]);

  useEffect(() => {
    if (!globeRef.current) return;
    globeRef.current.pointOfView({ lat: 18, lng: 0, altitude: 2.1 }, 0);
  }, [dimensions.width, dimensions.height]);

  return (
    <div ref={containerRef} className="h-[520px] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900/70">
      <div className="flex h-full w-full items-center justify-center">
      <Globe
        ref={globeRef}
        width={dimensions.width}
        height={dimensions.height}
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundColor="rgba(0,0,0,0)"
        pointsData={centeredPoints}
        pointLat="lat"
        pointLng="lng"
        pointLabel={(d: object) => {
          const p = d as GlobePoint;
          return `${p.title} | 热度:${p.hot_score} | 重要:${p.importance_score}`;
        }}
        pointAltitude={(d: object) => {
          const p = d as GlobePoint;
          return Math.max(0.05, p.importance_score / 600);
        }}
        pointColor={(d: object) => {
          const p = d as GlobePoint;
          if (p.level === "S") return "#ef4444";
          if (p.level === "A") return "#f59e0b";
          if (p.level === "B") return "#22c55e";
          return "#38bdf8";
        }}
      />
      </div>
    </div>
  );
}
