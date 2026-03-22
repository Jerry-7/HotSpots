import { GlobeView } from "../components/globe-view";
import { getGlobePoints, getHotspots } from "../lib/api";

const windows = ["1h", "6h", "24h", "7d", "30d"];

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ window?: string }>;
}) {
  const params = await searchParams;
  const window = windows.includes(params.window || "") ? (params.window as string) : "24h";
  let points: any[] = [];
  let hotspots: any[] = [];
  let loadError = "";

  try {
    [points, hotspots] = await Promise.all([getGlobePoints(window), getHotspots(window)]);
  } catch {
    loadError = "数据加载失败，请确认后端服务正常并稍后重试。";
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-xl font-semibold">全球热点地球</h1>
          <div className="flex gap-2 text-sm">
            {windows.map((item) => (
              <a
                key={item}
                href={`/?window=${item}`}
                className={`rounded-lg px-3 py-1 ${item === window ? "bg-teal-500 text-white" : "bg-slate-700 text-slate-200"}`}
              >
                {item}
              </a>
            ))}
          </div>
        </div>
        <GlobeView points={points} />
      </section>

      <section className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="mb-3 text-lg font-semibold">热点流</h2>
        {loadError ? (
          <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{loadError}</div>
        ) : hotspots.length === 0 ? (
          <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-3 text-sm text-slate-300">暂无热点数据，先去配置页点击一键刷新。</div>
        ) : (
          <div className="grid gap-3">
            {hotspots.map((item: any) => (
              <article key={item.event_id} className="rounded-xl border border-slate-700 bg-slate-800/60 p-3">
                <div className="mb-1 flex items-center justify-between gap-4">
                  <h3 className="font-medium">{item.title}</h3>
                  <span className="rounded bg-amber-500/20 px-2 py-1 text-xs text-amber-300">{item.level}</span>
                </div>
                <p className="text-sm text-slate-300">{item.summary}</p>
                <div className="mt-2 text-xs text-slate-400">
                  {item.country} / {item.city} | 热度 {item.hot_score} | 重要性 {item.importance_score}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
