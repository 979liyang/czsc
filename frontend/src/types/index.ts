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
}
