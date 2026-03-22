import { getRankings } from "../../lib/api";

const windows = ["1h", "6h", "24h", "7d", "30d"];

export default async function RankingPage({
  searchParams,
}: {
  searchParams: Promise<{ window?: string }>;
}) {
  const params = await searchParams;
  const window = windows.includes(params.window || "") ? (params.window as string) : "24h";
  let rankings: any[] = [];
  let loadError = "";

  try {
    rankings = await getRankings(window);
  } catch {
    loadError = "榜单加载失败，请稍后重试。";
  }

  return (
    <section className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold">热度榜单</h1>
        <div className="flex gap-2 text-sm">
          {windows.map((item) => (
            <a
              key={item}
              href={`/ranking?window=${item}`}
              className={`rounded-lg px-3 py-1 ${item === window ? "bg-teal-500 text-white" : "bg-slate-700 text-slate-200"}`}
            >
              {item}
            </a>
          ))}
        </div>
      </div>
      {loadError ? (
        <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-3 text-sm text-rose-200">{loadError}</div>
      ) : rankings.length === 0 ? (
        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-3 text-sm text-slate-300">暂无榜单数据，先去配置页刷新数据。</div>
      ) : (
        <div className="space-y-2">
          {rankings.map((item: any, idx: number) => (
            <div key={item.event_id} className="flex items-center justify-between rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2">
              <div>
                <div className="font-medium">
                  #{idx + 1} {item.title}
                </div>
                <div className="text-xs text-slate-400">
                  {item.topic} | {item.country}
                </div>
              </div>
              <div className="text-right text-sm text-slate-200">
                <div>热度 {item.hot_score}</div>
                <div>重要 {item.importance_score}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
