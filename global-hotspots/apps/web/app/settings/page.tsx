"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  getRuntimeProxy,
  getSourceConnectivity,
  listProviders,
  listSources,
  previewSource,
  refreshEvents,
  setRuntimeProxy,
  upsertProvider,
  updateSourceConfig,
  type ProviderItem,
  type SourceConnectivityItem,
  type SourcePreviewOut,
  type SourceItem,
} from "../../lib/api";

export default function SettingsPage() {
  const [provider, setProvider] = useState("openrouter");
  const [model, setModel] = useState("gpt-4o-mini");
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [message, setMessage] = useState("");
  const [providers, setProviders] = useState<ProviderItem[]>([]);
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [sourceMessage, setSourceMessage] = useState("");
  const [refreshMessage, setRefreshMessage] = useState("");
  const [proxyUrl, setProxyUrl] = useState("");
  const [proxyMessage, setProxyMessage] = useState("");
  const [connectivity, setConnectivity] = useState<Record<number, SourceConnectivityItem>>({});
  const [previewData, setPreviewData] = useState<Record<number, SourcePreviewOut>>({});
  const [previewMessage, setPreviewMessage] = useState<Record<number, string>>({});

  async function refreshAll() {
    setLoading(true);
    try {
      const [providerList, sourceList, connectivityList, proxy] = await Promise.all([
        listProviders(),
        listSources(),
        getSourceConnectivity(),
        getRuntimeProxy(),
      ]);
      setProviders(providerList);
      setSources(sourceList);
      const byId: Record<number, SourceConnectivityItem> = {};
      for (const item of connectivityList) {
        byId[item.source_id] = item;
      }
      setConnectivity(byId);
      setProxyUrl(proxy.source_proxy_url || "");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshAll();
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setMessage("保存中...");
    try {
      await upsertProvider({
        provider,
        api_key: apiKey,
        model,
        base_url: baseUrl.trim() || null,
        is_default: true,
      });
      setApiKey("");
      setMessage("已保存");
      await refreshAll();
    } catch {
      setMessage("保存失败");
    }
  }

  function updateSourceDraft(sourceId: number, patch: Partial<SourceItem>) {
    setSources((prev) => prev.map((item) => (item.source_id === sourceId ? { ...item, ...patch } : item)));
  }

  async function saveSource(sourceId: number) {
    const source = sources.find((item) => item.source_id === sourceId);
    if (!source) return;
    setSourceMessage(`保存 ${source.name} 中...`);
    try {
      const updated = await updateSourceConfig(sourceId, {
        enabled: source.enabled,
        weight: source.weight,
        crawl_interval_minutes: source.crawl_interval_minutes,
        keyword_allowlist: source.keyword_allowlist,
        keyword_blocklist: source.keyword_blocklist,
      });
      setSources((prev) => prev.map((item) => (item.source_id === sourceId ? updated : item)));
      setSourceMessage(`已保存 ${updated.name}`);
    } catch {
      setSourceMessage(`保存 ${source.name} 失败`);
    }
  }

  async function onRefreshData() {
    setRefreshMessage("正在刷新采集与评分...");
    try {
      const result = await refreshEvents();
      setRefreshMessage(
        `刷新状态 ${result.status}：来源 ${result.ingest.sources || 0}，抓取 ${result.ingest.fetched || 0}，新增 ${result.ingest.inserted || 0}，评分 ${result.score.scores || 0}`,
      );
      await refreshAll();
    } catch {
      setRefreshMessage("刷新失败，请检查 API 与网络配置");
    }
  }

  async function onSaveProxy() {
    setProxyMessage("保存代理中...");
    try {
      const saved = await setRuntimeProxy(proxyUrl.trim() || null);
      setProxyUrl(saved.source_proxy_url || "");
      setProxyMessage("代理配置已保存");
      await refreshAll();
    } catch {
      setProxyMessage("保存代理失败");
    }
  }

  function connectivityText(item?: SourceConnectivityItem) {
    if (!item) return "未检测";
    if (item.status === "ok") return `连通 (${item.latency_ms || 0}ms)`;
    if (item.status === "skipped") return `跳过: ${item.detail || ""}`;
    return `失败: ${item.detail || ""}`;
  }

  function connectivityClass(item?: SourceConnectivityItem) {
    if (!item) return "text-slate-400";
    if (item.status === "ok") return "text-emerald-300";
    if (item.status === "skipped") return "text-amber-300";
    return "text-rose-300";
  }

  async function onPreviewSource(sourceId: number) {
    setPreviewMessage((prev) => ({ ...prev, [sourceId]: "测试拉取中..." }));
    try {
      const data = await previewSource(sourceId, 5);
      setPreviewData((prev) => ({ ...prev, [sourceId]: data }));
      setPreviewMessage((prev) => ({ ...prev, [sourceId]: data.status === "ok" ? `拉取成功，预览 ${data.count} 条` : `拉取失败: ${data.detail || ""}` }));
    } catch {
      setPreviewMessage((prev) => ({ ...prev, [sourceId]: "拉取失败，请检查网络/代理/来源地址" }));
    }
  }

  return (
    <section className="grid gap-6">
      <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4 md:max-w-3xl">
        <h1 className="mb-3 text-xl font-semibold">AI Provider Key</h1>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="rounded-lg bg-cyan-600 px-3 py-2 text-sm text-white hover:bg-cyan-500"
            onClick={() => void onRefreshData()}
          >
            一键刷新热点数据
          </button>
          {refreshMessage ? <span className="text-sm text-cyan-300">{refreshMessage}</span> : null}
        </div>
        <div className="mb-4 rounded-xl border border-slate-700 bg-slate-800/40 p-3">
          <div className="mb-2 text-sm font-medium text-slate-100">采集代理（HTTP/HTTPS）</div>
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={proxyUrl}
              onChange={(e) => setProxyUrl(e.target.value)}
              className="min-w-[320px] flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
              placeholder="例如: http://127.0.0.1:7890"
            />
            <button type="button" onClick={() => void onSaveProxy()} className="rounded-lg bg-indigo-600 px-3 py-2 text-sm text-white">
              保存代理
            </button>
          </div>
          {proxyMessage ? <div className="mt-2 text-sm text-indigo-300">{proxyMessage}</div> : null}
        </div>
        <form onSubmit={onSubmit} className="space-y-3">
          <input
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2"
            placeholder="provider"
          />
          <input
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2"
            placeholder="model"
          />
          <input
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2"
            placeholder="base url (optional)"
          />
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2"
            placeholder="API key"
          />
          <button className="rounded-lg bg-teal-500 px-4 py-2 text-white">保存</button>
          <p className="text-sm text-slate-300">{message}</p>
        </form>
        <div className="mt-4 border-t border-slate-700 pt-3">
          <h2 className="mb-2 text-sm font-semibold text-slate-200">已配置 Provider</h2>
          {loading ? (
            <p className="text-sm text-slate-400">加载中...</p>
          ) : providers.length === 0 ? (
            <p className="text-sm text-slate-400">暂无配置</p>
          ) : (
            <div className="space-y-2">
              {providers.map((item) => (
                <div key={item.provider} className="rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{item.provider}</span>
                    {item.is_default ? <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-300">默认</span> : null}
                  </div>
                  <div className="text-slate-300">model: {item.model}</div>
                  <div className="text-slate-400">key: {item.key_preview}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-700 bg-slate-900/60 p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">来源配置</h2>
          <button
            className="rounded-lg border border-slate-600 px-3 py-1 text-sm text-slate-200 hover:bg-slate-800"
            onClick={() => void refreshAll()}
            type="button"
          >
            刷新
          </button>
        </div>
        <p className="mb-3 text-sm text-slate-300">可直接配置来源开关、权重、抓取频率和关键词黑白名单。</p>
        {sourceMessage ? <p className="mb-3 text-sm text-emerald-300">{sourceMessage}</p> : null}
        <div className="space-y-3">
          {sources.map((item) => (
            <div key={item.source_id} className="rounded-xl border border-slate-700 bg-slate-800/50 p-3">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-slate-400">
                    {item.source_type} | {item.region} | {item.language} | 可靠性 {item.reliability_score}
                  </div>
                  <div className={`mt-1 text-xs ${connectivityClass(connectivity[item.source_id])}`}>{connectivityText(connectivity[item.source_id])}</div>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={item.enabled}
                    onChange={(e) => updateSourceDraft(item.source_id, { enabled: e.target.checked })}
                  />
                  启用
                </label>
              </div>

              <div className="grid gap-2 md:grid-cols-2">
                <label className="text-sm text-slate-300">
                  权重
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={item.weight}
                    onChange={(e) => updateSourceDraft(item.source_id, { weight: Number(e.target.value) || 0 })}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  />
                </label>
                <label className="text-sm text-slate-300">
                  抓取间隔（分钟）
                  <input
                    type="number"
                    min="1"
                    value={item.crawl_interval_minutes}
                    onChange={(e) =>
                      updateSourceDraft(item.source_id, { crawl_interval_minutes: Math.max(1, Number(e.target.value) || 1) })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  />
                </label>
                <label className="text-sm text-slate-300 md:col-span-2">
                  关键词白名单（逗号分隔）
                  <input
                    value={item.keyword_allowlist.join(",")}
                    onChange={(e) =>
                      updateSourceDraft(item.source_id, {
                        keyword_allowlist: e.target.value
                          .split(",")
                          .map((v) => v.trim())
                          .filter(Boolean),
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  />
                </label>
                <label className="text-sm text-slate-300 md:col-span-2">
                  关键词黑名单（逗号分隔）
                  <input
                    value={item.keyword_blocklist.join(",")}
                    onChange={(e) =>
                      updateSourceDraft(item.source_id, {
                        keyword_blocklist: e.target.value
                          .split(",")
                          .map((v) => v.trim())
                          .filter(Boolean),
                      })
                    }
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
                  />
                </label>
              </div>

              <div className="mt-3">
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => void saveSource(item.source_id)}
                    className="rounded-lg bg-teal-500 px-4 py-2 text-sm text-white"
                  >
                    保存来源配置
                  </button>
                  <button
                    type="button"
                    onClick={() => void onPreviewSource(item.source_id)}
                    className="rounded-lg bg-sky-600 px-4 py-2 text-sm text-white"
                  >
                    测试拉取
                  </button>
                </div>
                {previewMessage[item.source_id] ? <div className="mt-2 text-xs text-sky-300">{previewMessage[item.source_id]}</div> : null}
                {previewData[item.source_id]?.items?.length ? (
                  <div className="mt-2 space-y-2 rounded-lg border border-slate-700 bg-slate-900/70 p-2">
                    {previewData[item.source_id].items.map((preview, idx) => (
                      <div key={`${item.source_id}-${idx}`} className="rounded border border-slate-700 bg-slate-800/60 p-2">
                        <div className="text-sm font-medium text-slate-100">{preview.title}</div>
                        <div className="mt-1 text-xs text-slate-300">{preview.summary}</div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
