"use client";

import dynamic from "next/dynamic";

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
  return (
    <div className="h-[520px] overflow-hidden rounded-2xl border border-slate-700 bg-slate-900/70">
      <Globe
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
        backgroundColor="rgba(0,0,0,0)"
        pointsData={points}
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
  );
}
