/**
 * TradingView Charting Library Datafeed（UDF 风格）。
 *
 * 说明：
 * - 后端实现的 UDF 端点：/api/v1/tv/*
 * - 本 datafeed 只实现历史数据（getBars），实时订阅为 no-op
 * - 分钟级别：只请求一次 /tv/minute-bars（最近 3 个月），之后从内存返回；返回给库的 bars 严格在 [from,to) 内，符合 charting_library 要求
 * - 日/周/月：请求 /tv/history
 */
import dayjs from "dayjs";
import { da } from "element-plus/es/locales.mjs";
type OnReadyCallback = (config: any) => void;
type ResolveCallback = (symbolInfo: any) => void;
type ErrorCallback = (reason: string) => void;
type HistoryCallback = (bars: any[], meta: { noData: boolean; nextTime?: number }) => void;

/**
 * 将 periodParams.from/to 统一为 Unix 秒。
 * datafeed-api：PeriodParams 为 Unix timestamp，库可能传秒或毫秒（Bar.time 为毫秒）。
 */
function toUnixSeconds(msOrSec: number): number {
  const v = Number(msOrSec);
  if (!Number.isFinite(v)) return 0;
  return v >= 1e12 ? Math.floor(v / 1000) : Math.floor(v);
}

function normalizeNextTimeToMs(nextTime: any): number | undefined {
  if (nextTime === null || nextTime === undefined) return undefined;
  const v = Number(nextTime);
  if (!Number.isFinite(v)) return undefined;
  // 兼容后端返回秒（< 1e12）与毫秒（>= 1e12）
  return v < 1e12 ? v * 1000 : v;
}

/**
 * 将后端 K 线时间 t 统一为 Bar.time（UTC 毫秒）。
 * 后端通常为 Unix 秒，若误传毫秒也兼容。
 */
function barTimeToMs(ts: unknown): number {
  const v = Number(ts);
  if (!Number.isFinite(v)) return 0;
  return v >= 1e12 ? Math.floor(v) : Math.floor(v * 1000);
}

/** 校验 Bar：time 为正整数毫秒，OHLC 为有限数 */
function isValidBar(b: { time: number; open: number; high: number; low: number; close: number }): boolean {
  const t = Math.floor(b.time);
  return (
    t === b.time &&
    t > 0 &&
    Number.isFinite(b.open) &&
    Number.isFinite(b.high) &&
    Number.isFinite(b.low) &&
    Number.isFinite(b.close)
  );
}

/** 构造库要求的 Bar 对象，仅含 time/open/high/low/close/volume；OHLC 必须为有限数否则 K 线不渲染 */
function toChartBar(
  time: number,
  open: number,
  high: number,
  low: number,
  close: number,
  volume: number
): { time: number; open: number; high: number; low: number; close: number; volume: number } {
  return {
    time: Math.floor(time),
    open: Number.isFinite(open) ? open : 0,
    high: Number.isFinite(high) ? high : 0,
    low: Number.isFinite(low) ? low : 0,
    close: Number.isFinite(close) ? close : 0,
    volume: Number.isFinite(volume) && volume >= 0 ? volume : 0,
  };
}

/**
 * 库内部会用 state 做 schema 校验；若存在 unknown/object 等类型会打警告。
 * 这里只返回 LibrarySymbolInfo 中明确需要的字段，且全部为 string | number | boolean | string[]，不传 undefined/null/嵌套对象。
 */
function normalizeSymbolInfo(raw: Record<string, unknown>): Record<string, string | number | boolean | string[]> {
  const str = (v: unknown) => (v != null ? String(v) : '');
  const num = (v: unknown, def: number) => (v != null && Number.isFinite(Number(v)) ? Number(v) : def);
  const bool = (v: unknown): boolean => v === true || v === 'true' || v === 1;
  const arr = (v: unknown): string[] =>
    Array.isArray(v) ? v.map((x) => String(x)).filter(Boolean) : [];
  const format = raw.format === 'volume' ? 'volume' : 'price';
  const dataStatus =
    raw.data_status === 'streaming' || raw.data_status === 'delayed_streaming'
      ? (raw.data_status as 'streaming' | 'delayed_streaming')
      : 'endofday';
  return {
    name: str(raw.name),
    ticker: str(raw.ticker || raw.name),
    description: str(raw.description || raw.name),
    type: str(raw.type || 'stock'),
    session: str(raw.session || '0930-1130,1300-1500'),
    timezone: str(raw.timezone || 'Asia/Shanghai'),
    exchange: str(raw.exchange || ''),
    listed_exchange: str(raw.listed_exchange || raw.exchange || ''),
    format,
    minmov: num(raw.minmov, 1),
    pricescale: num(raw.pricescale, 100),
    has_intraday: true,
    intraday_multipliers: arr(raw.intraday_multipliers).length ? arr(raw.intraday_multipliers) : ['1', '5', '15', '30', '60'],
    has_daily: bool(raw.has_daily),
    has_weekly_and_monthly: bool(raw.has_weekly_and_monthly),
    supported_resolutions: arr(raw.supported_resolutions).length ? arr(raw.supported_resolutions) : ['1', '5', '15', '30', '60', 'D', 'W', 'M'],
    volume_precision: num(raw.volume_precision, 0),
    data_status: dataStatus,
  };
}

/** 分钟级别 getBars 缓存：同一 symbol+resolution 下已返回的 3 个月窗口 */
interface MinuteCacheEntry {
  fromSec: number;
  toSec: number;
  bars: { time: number; open: number; high: number; low: number; close: number; volume: number }[];
}

/**
 * 调用 onResult：有 bars 时同步调用以便库立即渲染，无数据时延迟调用避免库内重入导致栈溢出。
 */
function invokeHistoryCallback(
  onResult: HistoryCallback,
  bars: { time: number; open: number; high: number; low: number; close: number; volume: number }[],
  meta: { noData: boolean; nextTime?: number }
): void {
  if (bars.length > 0) {
    onResult(bars, meta);
  } else {
    setTimeout(() => onResult(bars, meta), 0);
  }
}

export function createUdfDatafeed(baseUrl: string = '/api/v1') {
  const cfgUrl = `${baseUrl}/tv/config`;
  const searchUrl = `${baseUrl}/tv/search`;
  const symbolsUrl = `${baseUrl}/tv/symbols`;
  const historyUrl = `${baseUrl}/tv/history`;
  const minuteBarsUrl = `${baseUrl}/tv/minute-bars`;

  const minuteCache = new Map<string, MinuteCacheEntry>();

  return {
    getServerTime: (callback: (serverTime: number) => void) => {
      fetch(`${baseUrl}/tv/time`)
        .then((r) => r.json())
        .then((n) => callback(Number(n)))
        .catch(() => callback(Math.floor(Date.now() / 1000)));
    },

    onReady: async (cb: OnReadyCallback) => {
      try {
        const res = await fetch(cfgUrl);
        const json = await res.json();
        cb(json);
      } catch (e) {
        console.warn('[tv] onReady failed', e);
        cb({
          supports_search: true,
          supports_group_request: false,
          supports_marks: false,
          supports_timescale_marks: false,
          supports_time: true,
          supported_resolutions: ['1', '5', '15', '30', '60', 'D', 'W', 'M'],
        });
      }
    },

    searchSymbols: async (
      userInput: string,
      _exchange: string,
      _symbolType: string,
      onResult: (r: { symbol: string; description: string; exchange: string; ticker?: string; type: string }[]) => void
    ) => {
      try {
        const url = new URL(searchUrl, window.location.origin);
        url.searchParams.set('query', userInput || '');
        url.searchParams.set('limit', '30');
        const res = await fetch(url.toString());
        const json = await res.json();
        const raw = Array.isArray(json) ? json : [];
        const items = raw.map((item: any) => ({
          symbol: item.symbol ?? item.ticker ?? item.full_name ?? '',
          description: item.description ?? item.symbol ?? '',
          exchange: item.exchange ?? '',
          ticker: item.ticker ?? item.symbol,
          type: item.type ?? 'stock',
        }));
        onResult(items);
      } catch (e) {
        console.warn('[tv] searchSymbols failed', e);
        onResult([]);
      }
    },

    resolveSymbol: async (symbolName: string, onResolve: ResolveCallback, onError: ErrorCallback) => {
      try {
        const url = new URL(symbolsUrl, window.location.origin);
        url.searchParams.set('symbol', symbolName);
        const res = await fetch(url.toString());
        const json = await res.json();
        onResolve(normalizeSymbolInfo(json || {}) as any);
      } catch (e) {
        console.warn('[tv] resolveSymbol failed', e);
        onError('resolveSymbol failed');
      }
    },

    getBars: async (
      symbolInfo: any,
      resolution: string,
      periodParams: { from: number; to: number; countBack?: number; firstDataRequest?: boolean },
      onResult: HistoryCallback,
      onError: ErrorCallback
    ) => {
      console.log('getBars', symbolInfo, resolution, dayjs(periodParams.from * 1000).format('YYYY-MM-DD HH:mm:ss'),  dayjs(periodParams.to * 1000).format('YYYY-MM-DD HH:mm:ss'));
      try {
        const symbol = symbolInfo?.ticker || symbolInfo?.name || symbolInfo?.symbol || '';
        const toSec = toUnixSeconds(periodParams.to);
        const requestFromSec = toUnixSeconds(periodParams.from);
        const resUpper = (resolution || '').trim().toUpperCase();
        const isMinute = /^[0-9]+$/.test(resUpper);
        const reqFromMs = requestFromSec * 1000;
        const reqToMs = toSec * 1000;

        if (isMinute) {
          const url = new URL(minuteBarsUrl, window.location.origin);
          url.searchParams.set('symbol', symbol);
          url.searchParams.set('resolution', resolution);
          url.searchParams.set('from', String(requestFromSec));
          url.searchParams.set('to', String(toSec));
          const res = await fetch(url.toString());
          const json = await res.json();
          console.log('getBars - return', json);
          if (!json || json.s !== 'ok') {
            invokeHistoryCallback(onResult, [], {
              noData: true,
              nextTime: normalizeNextTimeToMs(json?.nextTime),
            });
            return;
          }
          const tArr = Array.isArray(json.t) ? json.t : [];
          const oArr = Array.isArray(json.o) ? json.o : [];
          const hArr = Array.isArray(json.h) ? json.h : [];
          const lArr = Array.isArray(json.l) ? json.l : [];
          const cArr = Array.isArray(json.c) ? json.c : [];
          const vArr = Array.isArray(json.v) ? json.v : [];
          const len = Math.min(tArr.length, oArr.length, hArr.length, lArr.length, cArr.length, vArr.length);
          const allBars: { time: number; open: number; high: number; low: number; close: number; volume: number }[] = [];
          for (let i = 0; i < len; i++) {
            const bar = toChartBar(
              barTimeToMs(tArr[i]),
              Number(oArr[i]),
              Number(hArr[i]),
              Number(lArr[i]),
              Number(cArr[i]),
              Number(vArr[i] ?? 0)
            );
            if (isValidBar(bar)) allBars.push(bar);
          }
          allBars.sort((a, b) => a.time - b.time);
          let bars = allBars.filter((b) => b.time >= reqFromMs && b.time < reqToMs);
          const useAllBars =
            (periodParams.firstDataRequest && allBars.length > 0) || (bars.length === 0 && allBars.length > 0);
          if (useAllBars) bars = allBars;
          console.log('getBars', bars.length);
          // 首次请求：优先返回请求区间内的 bars；若无则返回全部，让库先写入缓存
          const inRange = allBars.filter((b) => b.time >= reqFromMs && b.time < reqToMs);
          const toReturn = inRange.length > 0 ? inRange : allBars;
          // 传副本，避免库内部修改影响缓存
          const barsCopy = toReturn.map((b) => ({ ...b }));
          invokeHistoryCallback(onResult, barsCopy, { noData: barsCopy.length === 0 });
          return;
        }

        // 日/周/月：走 /tv/history
        const url = new URL(historyUrl, window.location.origin);
        url.searchParams.set('symbol', symbol);
        url.searchParams.set('resolution', resolution);
        url.searchParams.set('from', String(requestFromSec));
        url.searchParams.set('to', String(toSec));
        if (periodParams.countBack) url.searchParams.set('countback', String(periodParams.countBack));
        const res = await fetch(url.toString());
        const json = await res.json();
        if (!json || json.s !== 'ok') {
          invokeHistoryCallback(onResult, [], {
            noData: true,
            nextTime: normalizeNextTimeToMs(json?.nextTime),
          });
          return;
        }
        const tArr = Array.isArray(json.t) ? json.t : [];
        const oArr = Array.isArray(json.o) ? json.o : [];
        const hArr = Array.isArray(json.h) ? json.h : [];
        const lArr = Array.isArray(json.l) ? json.l : [];
        const cArr = Array.isArray(json.c) ? json.c : [];
        const vArr = Array.isArray(json.v) ? json.v : [];
        const len = Math.min(tArr.length, oArr.length, hArr.length, lArr.length, cArr.length, vArr.length);
        const allBars: { time: number; open: number; high: number; low: number; close: number; volume: number }[] = [];
        for (let i = 0; i < len; i++) {
          const bar = toChartBar(
            barTimeToMs(tArr[i]),
            Number(oArr[i]),
            Number(hArr[i]),
            Number(lArr[i]),
            Number(cArr[i]),
            Number(vArr[i] ?? 0)
          );
          if (isValidBar(bar)) allBars.push(bar);
        }
        allBars.sort((a, b) => a.time - b.time);
        let bars = allBars.filter((b) => b.time >= reqFromMs && b.time < reqToMs);
        const useAllBars =
          (periodParams.firstDataRequest && allBars.length > 0) || (bars.length === 0 && allBars.length > 0);
        if (useAllBars) bars = allBars;
        console.log('getBars', bars.length);
        if (bars.length > 0) {
          invokeHistoryCallback(onResult, bars, { noData: false });
        } else {
          invokeHistoryCallback(onResult, [], {
            noData: true,
            nextTime: normalizeNextTimeToMs(json?.nextTime),
          });
        }
      } catch (e) {
        console.warn('[tv] getBars failed', e);
        onError('getBars failed');
      }
    },

    subscribeBars: (_symbolInfo: any, _resolution: string, _onTick: any, _listenerGuid: string) => {
      // 本地 demo 暂不支持实时订阅
    },

    unsubscribeBars: (_listenerGuid: string) => {
      // no-op
    },
  };
}

/** K 线 Bar 类型（time 为 UTC 毫秒） */
export type Bar = { time: number; open: number; high: number; low: number; close: number; volume: number };

/**
 * 拉取与 datafeed 相同数据源的 K 线，供前端指标（如 SMC）计算使用。
 * @param baseUrl 如 '/api/v1'
 * @param symbol 标的
 * @param resolution 周期 1/5/15/30/60/D/W/M
 * @param fromSec 开始时间 Unix 秒
 * @param toSec 结束时间 Unix 秒
 */
export async function fetchBars(
  baseUrl: string,
  symbol: string,
  resolution: string,
  fromSec: number,
  toSec: number
): Promise<Bar[]> {
  const historyUrl = `${baseUrl}/tv/history`;
  const minuteBarsUrl = `${baseUrl}/tv/minute-bars`;
  const resUpper = (resolution || '').trim().toUpperCase();
  const isMinute = /^[0-9]+$/.test(resUpper);
  const reqFromMs = fromSec * 1000;
  const reqToMs = toSec * 1000;

  const parseResponse = (json: any): Bar[] => {
    if (!json || json.s !== 'ok') return [];
    const tArr = Array.isArray(json.t) ? json.t : [];
    const oArr = Array.isArray(json.o) ? json.o : [];
    const hArr = Array.isArray(json.h) ? json.h : [];
    const lArr = Array.isArray(json.l) ? json.l : [];
    const cArr = Array.isArray(json.c) ? json.c : [];
    const vArr = Array.isArray(json.v) ? json.v : [];
    const len = Math.min(tArr.length, oArr.length, hArr.length, lArr.length, cArr.length, vArr.length);
    const out: Bar[] = [];
    for (let i = 0; i < len; i++) {
      const bar = toChartBar(
        barTimeToMs(tArr[i]),
        Number(oArr[i]),
        Number(hArr[i]),
        Number(lArr[i]),
        Number(cArr[i]),
        Number(vArr[i] ?? 0)
      );
      if (isValidBar(bar)) out.push(bar);
    }
    out.sort((a, b) => a.time - b.time);
    return out.filter((b) => b.time >= reqFromMs && b.time < reqToMs);
  };

  if (isMinute) {
    const url = new URL(minuteBarsUrl, window.location.origin);
    url.searchParams.set('symbol', symbol);
    url.searchParams.set('resolution', resolution);
    url.searchParams.set('from', String(fromSec));
    url.searchParams.set('to', String(toSec));
    const res = await fetch(url.toString());
    const json = await res.json();
    return parseResponse(json);
  }

  const url = new URL(historyUrl, window.location.origin);
  url.searchParams.set('symbol', symbol);
  url.searchParams.set('resolution', resolution);
  url.searchParams.set('from', String(fromSec));
  url.searchParams.set('to', String(toSec));
  const res = await fetch(url.toString());
  const json = await res.json();
  return parseResponse(json);
}

