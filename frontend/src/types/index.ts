/**
 * TypeScript类型定义
 */

export interface Bar {
  symbol: string;
  id: number;
  dt: string;
  freq: string;
  open: number;
  close: number;
  high: number;
  low: number;
  vol: number;
  amount: number;
}

export interface BI {
  symbol: string;
  sdt: string;
  edt: string;
  direction: '向上' | '向下';
  high: number;
  low: number;
  power: number;
}

export interface FX {
  symbol: string;
  dt: string;
  mark: '顶分型' | '底分型';
  high: number;
  low: number;
  fx: number;
  power_str: string;
  power_volume: number;
}

export interface ZS {
  symbol: string;
  sdt: string;
  edt: string;
  sdir: string;
  edir: string;
  zg: number;
  zd: number;
  gg: number;
  dd: number;
  zz: number;
  is_valid: boolean;
  len_bis: number;
}

export interface AnalysisRequest {
  symbol: string;
  freq: string;
  sdt: string;
  edt: string;
}

export interface AnalysisResponse {
  symbol: string;
  freq: string;
  bis: BI[];
  fxs: FX[];
  zss: ZS[];
  // 统计信息
  bars_raw_count?: number;
  bars_ubi_count?: number;
  fx_count?: number;
  finished_bi_count?: number;
  bi_count?: number;
  ubi_count?: number;
  last_bi_extend?: boolean;
  last_bi_direction?: string;
  last_bi_power?: number;
}

// TradingVue.js 相关类型定义
export interface TradingVueData {
  t: number; // 时间戳（毫秒）
  o: number; // 开盘价
  h: number; // 最高价
  l: number; // 最低价
  c: number; // 收盘价
  v: number; // 成交量
}

export interface TradingVueOverlay {
  name: string;
  type: string;
  data: Array<{
    time: number;
    price: number;
    [key: string]: any;
  }>;
  settings?: Record<string, any>;
}
