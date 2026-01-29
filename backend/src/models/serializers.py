# -*- coding: utf-8 -*-
"""
对象序列化工具

将czsc对象转换为字典格式，用于JSON传输。
"""
from typing import Dict, Any, List
from czsc.objects import RawBar, BI, FX, ZS, Signal


def serialize_raw_bar(bar: RawBar) -> Dict[str, Any]:
    """
    序列化RawBar对象

    :param bar: RawBar对象
    :return: 字典
    """
    return {
        'symbol': bar.symbol,
        'id': bar.id,
        'dt': bar.dt.isoformat() if hasattr(bar.dt, 'isoformat') else str(bar.dt),
        'freq': bar.freq.value,
        'open': bar.open,
        'close': bar.close,
        'high': bar.high,
        'low': bar.low,
        'vol': bar.vol,
        'amount': bar.amount,
    }


def serialize_bi(bi: BI) -> Dict[str, Any]:
    """
    序列化BI对象

    :param bi: BI对象
    :return: 字典
    """
    return {
        'symbol': bi.symbol,
        'sdt': bi.sdt.isoformat() if hasattr(bi.sdt, 'isoformat') else str(bi.sdt),
        'edt': bi.edt.isoformat() if hasattr(bi.edt, 'isoformat') else str(bi.edt),
        'direction': bi.direction.value,
        'high': bi.high,
        'low': bi.low,
        'power': bi.power,
    }


def serialize_fx(fx: FX) -> Dict[str, Any]:
    """
    序列化FX对象

    :param fx: FX对象
    :return: 字典
    """
    return {
        'symbol': fx.symbol,
        'dt': fx.dt.isoformat() if hasattr(fx.dt, 'isoformat') else str(fx.dt),
        'mark': fx.mark.value,
        'high': fx.high,
        'low': fx.low,
        'fx': fx.fx,
        'power_str': fx.power_str,
        'power_volume': fx.power_volume,
    }


def serialize_zs(zs: ZS) -> Dict[str, Any]:
    """
    序列化ZS对象

    :param zs: ZS对象
    :return: 字典
    """
    return {
        'symbol': zs.symbol,
        'sdt': zs.sdt.isoformat() if hasattr(zs.sdt, 'isoformat') else str(zs.sdt),
        'edt': zs.edt.isoformat() if hasattr(zs.edt, 'isoformat') else str(zs.edt),
        'sdir': zs.sdir.value,
        'edir': zs.edir.value,
        'zg': zs.zg,
        'zd': zs.zd,
        'gg': zs.gg,
        'dd': zs.dd,
        'zz': zs.zz,
        'is_valid': zs.is_valid,
        'len_bis': len(zs.bis),
    }


def serialize_signal(signal: Signal) -> Dict[str, Any]:
    """
    序列化Signal对象

    :param signal: Signal对象
    :return: 字典
    """
    return {
        'signal': signal.signal,
        'score': signal.score,
        'k1': signal.k1,
        'k2': signal.k2,
        'k3': signal.k3,
        'v1': signal.v1,
        'v2': signal.v2,
        'v3': signal.v3,
    }


def serialize_raw_bars(bars: List[RawBar]) -> List[Dict[str, Any]]:
    """序列化RawBar列表"""
    return [serialize_raw_bar(bar) for bar in bars]


def serialize_bis(bis: List[BI]) -> List[Dict[str, Any]]:
    """序列化BI列表"""
    return [serialize_bi(bi) for bi in bis]


def serialize_fxs(fxs: List[FX]) -> List[Dict[str, Any]]:
    """序列化FX列表"""
    return [serialize_fx(fx) for fx in fxs]


def serialize_zss(zss: List[ZS]) -> List[Dict[str, Any]]:
    """序列化ZS列表"""
    return [serialize_zs(zs) for zs in zss]
