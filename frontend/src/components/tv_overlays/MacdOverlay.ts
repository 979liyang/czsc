import { Overlay } from 'trading-vue-js';

/**
 * MACD 指标（offchart overlay）
 *
 * 数据格式：[[ts_ms, diff, dea, macd], ...]
 * - ts_ms: 毫秒时间戳
 * - diff/dea: 两条线
 * - macd: 柱状值（正负区分颜色）
 */
export default {
  name: 'MACD',
  mixins: [Overlay],
  methods: {
    meta_info() {
      return { author: 'npc-czsc', version: '0.1.0' };
    },
    use_for() {
      return ['MACD'];
    },
    y_range(hi: number, lo: number) {
      // 让 0 轴一定可见，并覆盖 diff/dea/macd
      const data = (this as any).$props.data || [];
      let maxV = -Infinity;
      let minV = Infinity;
      for (const p of data) {
        for (let i = 1; i <= 3; i++) {
          const v = p[i];
          if (v == null || Number.isNaN(v)) continue;
          maxV = Math.max(maxV, v);
          minV = Math.min(minV, v);
        }
      }
      if (!Number.isFinite(maxV) || !Number.isFinite(minV)) {
        return [hi, lo];
      }
      maxV = Math.max(maxV, 0);
      minV = Math.min(minV, 0);
      return [maxV, minV];
    },
    draw(ctx: CanvasRenderingContext2D) {
      const layout = (this as any).$props.layout;
      const data: Array<[number, number, number, number]> = (this as any).$props.data || [];
      if (!data.length) return;

      const colorUp = this.colorUp;
      const colorDw = this.colorDw;
      const colorDiff = this.colorDiff;
      const colorDea = this.colorDea;

      // histogram
      const y0 = layout.$2screen(0);
      ctx.lineWidth = 1;
      for (let i = 0; i < data.length; i++) {
        const p = data[i];
        const x = layout.t2screen(p[0]);
        const y = layout.$2screen(p[3]);
        const w = this.barWidth;
        ctx.strokeStyle = p[3] >= 0 ? colorUp : colorDw;
        ctx.beginPath();
        ctx.moveTo(x, y0);
        ctx.lineTo(x, y);
        ctx.stroke();

        // 画粗一点：两侧再补一条
        if (w > 1) {
          ctx.beginPath();
          ctx.moveTo(x - 1, y0);
          ctx.lineTo(x - 1, y);
          ctx.stroke();
        }
      }

      // diff line
      ctx.strokeStyle = colorDiff;
      ctx.lineWidth = this.lineWidth;
      ctx.beginPath();
      let started = false;
      for (const p of data) {
        const x = layout.t2screen(p[0]);
        const y = layout.$2screen(p[1]);
        if (p[1] == null || y !== y) continue;
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // dea line
      ctx.strokeStyle = colorDea;
      ctx.lineWidth = this.lineWidth;
      ctx.beginPath();
      started = false;
      for (const p of data) {
        const x = layout.t2screen(p[0]);
        const y = layout.$2screen(p[2]);
        if (p[2] == null || y !== y) continue;
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();
    },
    legend(values: any[]) {
      // values: [ts, diff, dea, macd]
      if (!values || values.length < 4) return [];
      return [
        { value: `DIFF:${Number(values[1]).toFixed(4)}`, color: this.colorDiff },
        { value: `DEA:${Number(values[2]).toFixed(4)}`, color: this.colorDea },
        { value: `MACD:${Number(values[3]).toFixed(4)}`, color: values[3] >= 0 ? this.colorUp : this.colorDw },
      ];
    },
  },
  computed: {
    sett() {
      return (this as any).$props.settings || {};
    },
    colorUp() {
      return this.sett.colorUp || '#F9293E';
    },
    colorDw() {
      return this.sett.colorDw || '#00aa3b';
    },
    colorDiff() {
      return this.sett.colorDiff || '#5691ce';
    },
    colorDea() {
      return this.sett.colorDea || '#ffb703';
    },
    lineWidth() {
      return this.sett.lineWidth || 1.0;
    },
    barWidth() {
      return this.sett.barWidth || 2;
    },
  },
};

