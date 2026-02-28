<template>
  <div class="shapes-demo h-[100vh] flex flex-col bg-[#1f212d]">
    <div class="flex items-center justify-between px-3 py-2 bg-[#262a35] border-b border-[#363a45] shrink-0">
      <span class="text-[#9ca3af] text-sm">图形参数调试 · 修改右侧参数可实时预览</span>
      <router-link to="/tv" class="text-[#60a5fa] text-sm hover:underline">返回 K 线图</router-link>
    </div>
    <div class="flex flex-1 min-h-0">
      <div class="chart-area flex-1 min-w-0">
        <TradingViewWidget
          symbol="000001.SZ"
          interval="1D"
          :smc-enabled="false"
          :czsc-bs-enabled="false"
          @chart-ready="onChartReady"
        />
      </div>
      <aside class="panel w-[320px] shrink-0 overflow-y-auto bg-[#262a35] border-l border-[#363a45] p-4">
        <h2 class="text-white font-semibold text-base mb-4">图形参数调整</h2>
        <p class="text-[#9ca3af] text-xs mb-4">
          修改下方参数后图表会实时重绘，用于调试 CZSC/SMC 等叠加样式。
        </p>

        <!-- 可绘制图形一览（来自 tv_overrides.md + README-shapes.md） -->
        <details class="mb-6 rounded border border-[#363a45] overflow-hidden">
          <summary class="px-3 py-2 bg-[#1f212d] text-[#e5e7eb] text-sm cursor-pointer select-none">
            可绘制图形一览（TradingView API）
          </summary>
          <div class="px-3 py-2 text-xs text-[#9ca3af] space-y-2 bg-[#1f212d]/80">
            <p class="font-medium text-[#d1d5db]">数据源标记（datafeed-api.d.ts）</p>
            <p>datafeed 不提供 createShape/createMultipointShape，仅提供两类标记：<strong>getMarks</strong> 返回 <code class="text-[#60a5fa]">Mark[]</code>（K 线柱标记）、<strong>getTimescaleMarks</strong> 返回 <code class="text-[#60a5fa]">TimescaleMark[]</code>（时间轴标记）。需在 DatafeedConfiguration 中设置 <code class="text-[#60a5fa]">supports_marks</code> / <code class="text-[#60a5fa]">supports_timescale_marks</code> 为 true。</p>
            <p>Mark 字段：id, time, color, text, label, labelFontColor, minSize, borderWidth, imageUrl 等。TimescaleMark 字段：id, time, color, labelFontColor, label, tooltip, shape, imageUrl 等。TimeScaleMarkShape 枚举：circle, earningUp, earningDown, earning。</p>
            <p class="font-medium text-[#d1d5db]">createShape（单点）</p>
            <p>arrow_up, arrow_down, flag, vertical_line, horizontal_line, long_position, short_position, icon, emoji, sticker, text, anchored_text, note, anchored_note。long_position/short_position 与 anchored_text/anchored_note 需 createAnchoredShape，本 Demo 仅做 createShape 单点类型。</p>
            <p class="font-medium text-[#d1d5db]">createMultipointShape（多点）</p>
            <p>trend_line, horizontal_ray, rectangle, triangle, circle, ellipse, arrow, ray, extended, polyline, path, curve, 以及 fib、pattern 等</p>
            <p class="font-medium text-[#d1d5db]">属性 override</p>
            <p>键名格式：<code class="text-[#60a5fa]">linetool&lt;工具名&gt;.&lt;属性&gt;</code>，完整列表见 <code class="text-[#60a5fa]">charting_library.d.ts</code>。</p>
            <p class="font-medium text-[#d1d5db]">本页已按 d.ts 全属性对接的图形</p>
            <p>text(linetooltext)、vertline(linetoolvertline)、circle(linetoolcircle)、triangle(linetooltriangle)、arrow(linetoolarrowmarkup/down)、矩形(linetoolrectangle)、水平射线(linetoolhorzray)、水平线(linetoolhorzline)、旗帜(linetoolflagmark) 等；对应 d.ts 接口见 README-shapes.md。未对接：createShape 之 icon、emoji、sticker、note；createMultipointShape 之 ellipse、ray、extended、polyline、path、curve；信号标记 price_label、arrow_marker、cross_line、signpost 等见 README-shapes.md §6.10。</p>
          </div>
        </details>

        <!-- 所有图形 d.ts DrawingOverrides 全量列表 -->
        <details class="mb-6 rounded border border-[#363a45] overflow-hidden">
          <summary class="px-3 py-2 bg-[#1f212d] text-[#e5e7eb] text-sm cursor-pointer select-none">
            所有图形（d.ts 全量 {{ ALL_LINETOOLS.length }} 个）
          </summary>
          <div class="px-3 py-2 text-xs bg-[#1f212d]/80 max-h-[280px] overflow-y-auto">
            <p class="text-[#9ca3af] mb-2">DrawingOverrides 全部接口，override 键前缀见「linetoolxxx」</p>
            <ul class="space-y-1 text-[#b0b5bb]">
              <li v-for="t in ALL_LINETOOLS" :key="t.prefix" class="flex justify-between gap-2">
                <span class="truncate">{{ t.name }}</span>
                <code class="text-[#60a5fa] shrink-0">{{ t.prefix }}</code>
              </li>
            </ul>
          </div>
        </details>

        <!-- 图形列表：默认只显示 title，点击展开当前并在 K 线图显示，其他收起且图上隐藏 -->
        <div
          v-for="s in SHAPE_SECTIONS"
          :key="s.key"
          class="mb-3 rounded border overflow-hidden"
          :class="activeShapeKey === s.key ? 'border-[#3b82f6] bg-[#1f212d]' : 'border-[#363a45] bg-[#1f212d]/50'"
        >
          <div
            class="flex items-center justify-between px-3 py-2 cursor-pointer select-none text-sm hover:bg-[#262a35]"
            :class="activeShapeKey === s.key ? 'text-[#60a5fa] font-medium' : 'text-[#e5e7eb]'"
            @click="toggleShape(s.key)"
          >
            <span>{{ s.title }}</span>
            <span class="text-[#6b7280] text-xs">{{ activeShapeKey === s.key ? '▼ 展开' : '▶ 收起' }}</span>
          </div>
          <div v-show="activeShapeKey === s.key" class="px-3 pb-3 pt-1 border-t border-[#363a45]">
            <!-- 单点文案：hAlign/vAlign 为相对锚点对齐；上方/下方+距离可配连接线 -->
            <template v-if="s.key === 'text'">
            <p class="text-[#6b7280] text-xs mb-2">hAlign/vAlign 为文案相对锚点对齐；居中对齐请选 center / middle。连接线长度与文案距连接线的距离可分别调节。</p>
              <p class="text-[#6b7280] text-xs mb-2">TextLineToolOverrides 全部 12 属性</p>
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">color</label>
              <input v-model="cfg.text.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fontsize</label>
              <input v-model.number="cfg.text.fontsize" type="number" min="8" max="24"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">bold</label>
              <input v-model="cfg.text.bold" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">italic</label>
              <input v-model="cfg.text.italic" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">backgroundColor</label>
              <input v-model="cfg.text.backgroundColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">backgroundTransparency</label>
              <input v-model.number="cfg.text.backgroundTransparency" type="number" min="0" max="100"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">borderColor</label>
              <input v-model="cfg.text.borderColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">drawBorder</label>
              <input v-model="cfg.text.drawBorder" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fillBackground</label>
              <input v-model="cfg.text.fillBackground" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fixedSize</label>
              <input v-model="cfg.text.fixedSize" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">wordWrap</label>
              <input v-model="cfg.text.wordWrap" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">wordWrapWidth</label>
              <input v-model.number="cfg.text.wordWrapWidth" type="number" min="50" max="500"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">内容</label>
              <input v-model="cfg.text.content" type="text" placeholder="中枢"
                class="flex-1 min-w-0 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">hAlign</label>
              <select v-model="cfg.text.hAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="left">left</option>
                <option value="center">center</option>
                <option value="right">right</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">vAlign</label>
              <select v-model="cfg.text.vAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="top">top</option>
                <option value="middle">middle</option>
                <option value="bottom">bottom</option>
              </select>
            </div>
            <p class="text-[#6b7280] text-xs">居中请选 center / middle，部分 TV 版本可能不生效</p>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">上下位置</label>
              <select v-model="cfg.text.verticalPlacement" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="on">锚点上（默认）</option>
                <option value="above">上方</option>
                <option value="below">下方</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">连接线长度(%)</label>
              <input v-model.number="cfg.text.connectorLengthPercent" type="number" min="0" max="20" step="0.5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
              <span class="text-[#6b7280] text-xs">锚点到线末端</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">文案距连接线(%)</label>
              <input v-model.number="cfg.text.textGapPercent" type="number" min="0" max="10" step="0.25"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
              <span class="text-[#6b7280] text-xs">线末端到文案</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">连接线距K线图(%)</label>
              <input v-model.number="cfg.text.connectorChartGapPercent" type="number" min="0" max="10" step="0.1"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
              <span class="text-[#6b7280] text-xs">起点距锚点价格%</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">连接线颜色</label>
              <input v-model="cfg.text.connectorLineColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">连接线宽</label>
              <input v-model.number="cfg.text.connectorLineWidth" type="number" min="0.5" max="4" step="0.5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
              </div>
            </template>
            <!-- 矩形 -->
            <template v-if="s.key === 'rect'">
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-20 text-[#9ca3af]">填充色</label>
              <input v-model="cfg.rect.fillColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-20 text-[#9ca3af]">边框色</label>
              <input v-model="cfg.rect.borderColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-20 text-[#9ca3af]">边框宽</label>
              <input v-model.number="cfg.rect.borderWidth" type="number" min="0" max="5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-20 text-[#9ca3af]">透明度</label>
              <input v-model.number="cfg.rect.transparency" type="number" min="0" max="100"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
              </div>
            </template>
            <!-- 水平线+文案 -->
            <template v-if="s.key === 'ray'">
              <p class="text-[#6b7280] text-xs mb-2">射线+文案</p>
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">虚线</label>
              <input v-model="cfg.ray.dashed" type="checkbox" class="rounded" />
              <span class="text-[#6b7280] text-xs">{{ cfg.ray.dashed ? '虚线' : '实线' }}</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">线段颜色</label>
              <input v-model="cfg.ray.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
              <input v-model="cfg.ray.color" type="text" class="flex-1 min-w-0 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">横向长度(天)</label>
              <input v-model.number="cfg.ray.lengthDays" type="number" min="1" max="30"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">线段粗度</label>
              <input v-model.number="cfg.ray.width" type="number" min="0.5" max="5" step="0.5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">文案内容</label>
              <input v-model="cfg.ray.labelText" type="text" placeholder="EQH"
                class="flex-1 min-w-0 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">文案对齐</label>
              <select v-model="cfg.ray.labelAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="left">线段左侧</option>
                <option value="middle">线段中间</option>
                <option value="right">线段右侧</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">上下位置</label>
              <select v-model="cfg.ray.labelVertical" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="above">线段上方</option>
                <option value="below">线段下方</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">距线段(%)</label>
              <input v-model.number="cfg.ray.labelOffsetPercent" type="number" min="0.05" max="5" step="0.1"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
              <span class="text-[#6b7280] text-xs">上方/下方距离</span>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">文案颜色</label>
              <input v-model="cfg.ray.labelColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
              <input v-model="cfg.ray.labelColor" type="text" class="flex-1 min-w-0 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">文案大小</label>
              <input v-model.number="cfg.ray.labelFontSize" type="number" min="8" max="24"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">水平居中</label>
              <select v-model="cfg.ray.labelHAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="left">左</option>
                <option value="center">居中</option>
                <option value="right">右</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-24 text-[#9ca3af]">垂直居中</label>
              <select v-model="cfg.ray.labelVAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="top">上</option>
                <option value="middle">居中</option>
                <option value="bottom">下</option>
              </select>
            </div>
              </div>
            </template>
            <!-- 箭头 -->
            <template v-if="s.key === 'arrow'">
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">direction</label>
              <select v-model="cfg.arrow.direction"
                class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="up">up (arrowmarkup)</option>
                <option value="down">down (arrowmarkdown)</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">color</label>
              <input v-model="cfg.arrow.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">arrowColor</label>
              <input v-model="cfg.arrow.arrowColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">bold</label>
              <input v-model="cfg.arrow.bold" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fontsize</label>
              <input v-model.number="cfg.arrow.fontsize" type="number" min="8" max="24"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">italic</label>
              <input v-model="cfg.arrow.italic" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">showLabel</label>
              <input v-model="cfg.arrow.showLabel" type="checkbox" class="rounded" />
            </div>
              </div>
            </template>
            <!-- 三角形 -->
            <template v-if="s.key === 'triangle'">
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">direction</label>
              <select v-model="cfg.triangle.direction"
                class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                <option value="up">up</option>
                <option value="down">down</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">color</label>
              <input v-model="cfg.triangle.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">backgroundColor</label>
              <input v-model="cfg.triangle.backgroundColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fillBackground</label>
              <input v-model="cfg.triangle.fillBackground" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">linewidth</label>
              <input v-model.number="cfg.triangle.linewidth" type="number" min="1" max="5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">transparency</label>
              <input v-model.number="cfg.triangle.transparency" type="number" min="0" max="100"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">sizePercent</label>
              <input v-model.number="cfg.triangle.sizePercent" type="number" min="0.1" max="3" step="0.1"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
              </div>
            </template>
            <!-- 竖线 -->
            <template v-if="s.key === 'verticalLine'">
              <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">linecolor</label>
              <input v-model="cfg.verticalLine.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">linewidth</label>
              <input v-model.number="cfg.verticalLine.width" type="number" min="1" max="5"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">虚线</label>
              <input v-model="cfg.verticalLine.dashed" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">bold</label>
              <input v-model="cfg.verticalLine.bold" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">extendLine</label>
              <input v-model="cfg.verticalLine.extendLine" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">fontsize</label>
              <input v-model.number="cfg.verticalLine.fontsize" type="number" min="8" max="24"
                class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">horzLabelsAlign</label>
              <input v-model="cfg.verticalLine.horzLabelsAlign" type="text"
                class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">italic</label>
              <input v-model="cfg.verticalLine.italic" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">showTime</label>
              <input v-model="cfg.verticalLine.showTime" type="checkbox" class="rounded" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">textcolor</label>
              <input v-model="cfg.verticalLine.textcolor" type="color" class="w-10 h-6 rounded cursor-pointer" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">textOrientation</label>
              <input v-model="cfg.verticalLine.textOrientation" type="text"
                class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
            <div class="flex items-center gap-2">
              <label class="w-28 text-[#9ca3af]">vertLabelsAlign</label>
              <input v-model="cfg.verticalLine.vertLabelsAlign" type="text"
                class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
            </div>
              </div>
            </template>
            <!-- 水平线 -->
            <template v-if="s.key === 'horizontalLine'">
              <div class="space-y-2 text-sm">
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">linecolor</label>
                  <input v-model="cfg.horizontalLine.linecolor" type="color" class="w-10 h-6 rounded cursor-pointer" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">linewidth</label>
                  <input v-model.number="cfg.horizontalLine.linewidth" type="number" min="1" max="5"
                    class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">linestyle</label>
                  <select v-model.number="cfg.horizontalLine.linestyle" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                    <option :value="0">实线</option>
                    <option :value="1">虚线</option>
                  </select>
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">bold</label>
                  <input v-model="cfg.horizontalLine.bold" type="checkbox" class="rounded" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">showPrice</label>
                  <input v-model="cfg.horizontalLine.showPrice" type="checkbox" class="rounded" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">fontsize</label>
                  <input v-model.number="cfg.horizontalLine.fontsize" type="number" min="8" max="24"
                    class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">textcolor</label>
                  <input v-model="cfg.horizontalLine.textcolor" type="color" class="w-10 h-6 rounded cursor-pointer" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">horzLabelsAlign</label>
                  <select v-model="cfg.horizontalLine.horzLabelsAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                    <option value="left">left</option>
                    <option value="center">center</option>
                    <option value="right">right</option>
                  </select>
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">vertLabelsAlign</label>
                  <select v-model="cfg.horizontalLine.vertLabelsAlign" class="flex-1 rounded px-2 py-1 bg-[#1f212d] text-white text-xs">
                    <option value="top">top</option>
                    <option value="middle">middle</option>
                    <option value="bottom">bottom</option>
                  </select>
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">italic</label>
                  <input v-model="cfg.horizontalLine.italic" type="checkbox" class="rounded" />
                </div>
              </div>
            </template>
            <!-- 旗帜 -->
            <template v-if="s.key === 'flag'">
              <div class="space-y-2 text-sm">
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">flagColor</label>
                  <input v-model="cfg.flag.flagColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">文案</label>
                  <input v-model="cfg.flag.content" type="text" placeholder="旗标"
                    class="flex-1 min-w-0 rounded px-2 py-1 bg-[#1f212d] text-white text-xs" />
                </div>
              </div>
            </template>
            <!-- 圆：仅边框与填充，无文字样式 -->
            <template v-if="s.key === 'circle'">
              <p class="text-[#6b7280] text-xs mb-2">仅边框与填充，无文字样式</p>
              <div class="space-y-2 text-sm">
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">color</label>
                  <input v-model="cfg.circle.color" type="color" class="w-10 h-6 rounded cursor-pointer" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">backgroundColor</label>
                  <input v-model="cfg.circle.backgroundColor" type="color" class="w-10 h-6 rounded cursor-pointer" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">fillBackground</label>
                  <input v-model="cfg.circle.fillBackground" type="checkbox" class="rounded" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">linewidth</label>
                  <input v-model.number="cfg.circle.linewidth" type="number" min="1" max="5"
                    class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
                </div>
                <div class="flex items-center gap-2">
                  <label class="w-28 text-[#9ca3af]">半径(%)</label>
                  <input v-model.number="cfg.circle.radiusPercent" type="number" min="0.5" max="10" step="0.5"
                    class="w-16 rounded px-2 py-1 bg-[#1f212d] text-white" />
                </div>
              </div>
            </template>
          </div>
        </div>

        <button
          type="button"
          class="w-full py-2 rounded bg-[#3b82f6] text-white text-sm hover:bg-[#2563eb]"
          @click="redraw"
        >
          刷新图形
        </button>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, ref, watch } from 'vue';
import TradingViewWidget from '../components/TradingViewWidget.vue';
import type { ChartShape, ChartPoint } from '../tv/chartShapes';
import { drawChartShapes, clearChartShapes } from '../tv/chartShapes';
import { fetchBars } from '../tv/udfDatafeed';
import type { Bar } from '../tv/udfDatafeed';

/** d.ts DrawingOverrides 全部接口名 → linetool 前缀（可不用但不能没有） */
const ALL_LINETOOLS: { name: string; prefix: string }[] = [
  'Fivepointspattern', 'Abcd', 'Anchoredvp', 'Anchoredvwap', 'Arc', 'Arrow', 'Arrowmarkdown', 'Arrowmarker',
  'Arrowmarkleft', 'Arrowmarkright', 'Arrowmarkup', 'Balloon', 'Barspattern', 'Beziercubic', 'Bezierquadro',
  'Brush', 'Callout', 'Circle', 'Comment', 'Crossline', 'Cypherpattern', 'Dateandpricerange', 'Daterange',
  'Disjointangle', 'Elliottcorrection', 'Elliottdoublecombo', 'Elliottimpulse', 'Elliotttriangle', 'Elliotttriplecombo',
  'Ellipse', 'Emoji', 'Execution', 'Extended', 'Fibchannel', 'Fibcircles', 'Fibretracement', 'Fibspeedresistancearcs',
  'Fibspeedresistancefan', 'Fibtimezone', 'Fibwedge', 'Flagmark', 'Flatbottom', 'Ganncomplex', 'Gannfan',
  'Gannfixed', 'Gannsquare', 'Ghostfeed', 'Headandshoulders', 'Highlighter', 'Horzline', 'Horzray', 'Icon',
  'Image', 'Infoline', 'Insidepitchfork', 'Order', 'Parallelchannel', 'Path', 'Pitchfan', 'Pitchfork',
  'Polyline', 'Position', 'Prediction', 'Pricelabel', 'Projection', 'Ray', 'Regressiontrend', 'Riskrewardlong',
  'Riskrewardshort', 'Rotatedrectangle', 'Schiffpitchfork', 'Schiffpitchfork2', 'Signpost', 'Sineline', 'Sticker',
  'Text', 'Textabsolute', 'Threedrivers', 'Timecycles', 'Trendangle', 'Trendbasedfibextension', 'Trendbasedfibtime',
  'Trendline', 'Triangle', 'Trianglepattern', 'Vertline',
].map((n) => ({ name: `${n}LineToolOverrides`, prefix: `linetool${n.toLowerCase()}` }));

/** 图形列表：默认收起，点击标题只展开当前项并在 K 线图上只显示该图形 */
const SHAPE_SECTIONS = [
  { key: 'text', title: '单点文案 linetooltext' },
  { key: 'rect', title: '矩形 linetoolrectangle' },
  { key: 'ray', title: '水平线+文案 linetoolhorzray' },
  { key: 'arrow', title: '箭头 linetoolarrowmarkup/down' },
  { key: 'triangle', title: '三角形 linetooltriangle' },
  { key: 'verticalLine', title: '竖线 linetoolvertline' },
  { key: 'horizontalLine', title: '水平线 linetoolhorzline' },
  { key: 'flag', title: '旗帜 linetoolflagmark' },
  { key: 'circle', title: '圆 linetoolcircle' },
] as const;
const activeShapeKey = ref<string | null>(null);

function toggleShape(key: string) {
  activeShapeKey.value = activeShapeKey.value === key ? null : key;
}

let widgetRef: any = null;
const entityIds = ref<string[]>([]);
const demoBars = ref<Bar[]>([]);

const cfg = reactive({
  text: {
    color: '#2962FF',
    fontsize: 14,
    bold: false,
    italic: false,
    backgroundColor: 'rgba(41, 98, 255, 0.25)',
    backgroundTransparency: 70,
    borderColor: '#707070',
    drawBorder: false,
    fillBackground: false,
    fixedSize: true,
    wordWrap: false,
    wordWrapWidth: 200,
    content: '中枢',
    hAlign: 'center' as 'left' | 'center' | 'right',
    vAlign: 'middle' as 'top' | 'middle' | 'bottom',
    verticalPlacement: 'on' as 'on' | 'above' | 'below',
    connectorLengthPercent: 2,
    textGapPercent: 0.5,
    connectorChartGapPercent: 1,
    connectorLineColor: '#2962FF',
    connectorLineWidth: 1,
  },
  rect: {
    fillColor: '#7b1fa2',
    borderColor: '#9c27b0',
    borderWidth: 0,
    transparency: 85,
  },
  ray: {
    dashed: false,
    color: '#2196f3',
    width: 1,
    lengthDays: 5,
    labelText: 'EQH',
    labelAlign: 'right' as 'middle' | 'right',
    labelVertical: 'above' as 'above' | 'below',
    labelOffsetPercent: 0.8,
    labelColor: '#2196f3',
    labelFontSize: 11,
    labelHAlign: 'center' as 'left' | 'center' | 'right',
    labelVAlign: 'middle' as 'top' | 'middle' | 'bottom',
  },
  arrow: {
    direction: 'down' as 'up' | 'down',
    arrowColor: '#CC2F3C',
    bold: false,
    color: '#CC2F3C',
    fontsize: 14,
    italic: false,
    showLabel: true,
  },
  verticalLine: {
    color: '#2962FF',
    width: 2,
    dashed: false,
    bold: false,
    extendLine: true,
    fontsize: 14,
    horzLabelsAlign: 'center',
    italic: false,
    showTime: true,
    textcolor: '#2962FF',
    textOrientation: 'vertical',
    vertLabelsAlign: 'middle',
  },
  circle: {
    backgroundColor: 'rgba(255, 152, 0, 0.2)',
    color: '#FF9800',
    fillBackground: true,
    linewidth: 2,
    radiusPercent: 2,
  },
  triangle: {
    direction: 'down' as 'up' | 'down',
    backgroundColor: 'rgba(8, 153, 129, 0.2)',
    color: '#089981',
    fillBackground: true,
    linewidth: 2,
    transparency: 80,
    sizePercent: 0.6,
  },
  horizontalLine: {
    linecolor: '#2962FF',
    linewidth: 2,
    linestyle: 0,
    bold: false,
    showPrice: true,
    fontsize: 12,
    textcolor: '#2962FF',
    horzLabelsAlign: 'center',
    vertLabelsAlign: 'middle',
    italic: false,
  },
  flag: {
    flagColor: '#2962FF',
    content: '旗标',
  },
});

function onChartReady(widget: any) {
  widgetRef = widget;
  loadBarsAndRedraw();
}

async function loadBarsAndRedraw() {
  const chart = widgetRef?.activeChart?.();
  if (!chart) return;
  let fromSec: number;
  let toSec: number;
  try {
    const range = chart.getVisibleRange?.();
    const from = Number(range?.from ?? 0);
    const to = Number(range?.to ?? from + 86400 * 365);
    fromSec = from >= 1e12 ? Math.floor(from / 1000) : Math.floor(from);
    toSec = to >= 1e12 ? Math.floor(to / 1000) : Math.floor(to);
  } catch {
    toSec = Math.floor(Date.now() / 1000);
    fromSec = toSec - 365 * 86400;
  }
  const bars = await fetchBars('/api/v1', '000001.SZ', 'D', fromSec, toSec);
  demoBars.value = bars.length ? bars.slice(0, 20) : [];
  redraw();
}

function buildShapes(): ChartShape[] {
  const bars = demoBars.value;
  const day = 86400;
  if (bars.length < 5) {
    const t = Math.floor(Date.now() / 1000) - 10 * day;
    const prices = [10.2, 10.5, 10.8, 10.4, 10.6, 10.5];
    return buildShapesFromPoints(
      prices.map((p, i) => ({ time: t + i * 2 * day, price: p })),
      []
    );
  }
  const b0 = bars[0];
  const b1 = bars[1];
  const b2 = bars[2];
  const b3 = bars[3];
  const b4 = bars[4];
  const mid = bars[Math.floor(bars.length / 2)];
  const toSec = (t: number) => Math.floor(t / 1000);
  const points: ChartPoint[] = [
    { time: toSec(b0.time), price: b0.high },
    { time: toSec(b1.time), price: b1.low },
    { time: toSec(b2.time), price: (b2.high + b2.low) / 2 },
    { time: toSec(b3.time), price: b3.high },
    { time: toSec(b4.time), price: b4.high },
    { time: toSec(mid.time), price: (mid.high + mid.low) / 2 },
  ];
  return buildShapesFromPoints(points, bars);
}

/** bars 可选，用于文案连接线：上方时锚点为 K 线最高点、下方时为最低点，并加间距防重叠 */
function buildShapesFromPoints(
  pt: ChartPoint[],
  bars?: { time: number; high: number; low: number }[]
): ChartShape[] {
  const [, p1, p2, p3, p4, pMid] = pt;
  const day = 86400;
  const shapes: ChartShape[] = [];
  const key = activeShapeKey.value;
  if (!key) return shapes;

  if (key === 'text' && p1) {
    const anchor = p1;
    const placement = cfg.text.verticalPlacement ?? 'on';
    const connPct = (cfg.text.connectorLengthPercent ?? 0) / 100;
    const gapPct = (cfg.text.textGapPercent ?? 0) / 100;
    const gapChartPct = (cfg.text.connectorChartGapPercent ?? 1) / 100;
    const anchorTimeSec = anchor.time;
    const barAtAnchor =
      bars?.find((b) => Math.floor(b.time / 1000) === anchorTimeSec);
    const anchorPrice =
      placement === 'above'
        ? (barAtAnchor?.high ?? anchor.price)
        : placement === 'below'
          ? (barAtAnchor?.low ?? anchor.price)
          : anchor.price;
    let lineStart: ChartPoint;
    let lineEnd: ChartPoint;
    let textPoint: ChartPoint;
    if (placement === 'above') {
      lineStart = {
        time: anchor.time,
        price: anchorPrice + anchorPrice * gapChartPct,
      };
      lineEnd = {
        time: anchor.time,
        price: lineStart.price + anchorPrice * connPct,
      };
      textPoint = {
        time: anchor.time,
        price: lineEnd.price + anchorPrice * gapPct,
      };
    } else if (placement === 'below') {
      lineStart = {
        time: anchor.time,
        price: anchorPrice - anchorPrice * gapChartPct,
      };
      lineEnd = {
        time: anchor.time,
        price: lineStart.price - anchorPrice * connPct,
      };
      textPoint = {
        time: anchor.time,
        price: lineEnd.price - anchorPrice * gapPct,
      };
    } else {
      lineStart = anchor;
      lineEnd = anchor;
      textPoint = anchor;
    }
    const needConnector =
      (placement === 'above' || placement === 'below') && connPct > 0;
    if (needConnector) {
      shapes.push({
        kind: 'line',
        p1: lineStart,
        p2: lineEnd,
        style: {
          color: cfg.text.connectorLineColor ?? cfg.text.color,
          width: cfg.text.connectorLineWidth ?? 1,
        },
        connectorChartGapPercent: 0,
      });
    }
    shapes.push({
      kind: 'text',
      point: textPoint,
      text: cfg.text.content || '文案',
      style: {
        color: cfg.text.color,
        fontsize: cfg.text.fontsize,
        fontSize: cfg.text.fontsize,
        bold: cfg.text.bold,
        italic: cfg.text.italic,
        backgroundColor: cfg.text.backgroundColor,
        backgroundTransparency: cfg.text.backgroundTransparency,
        borderColor: cfg.text.borderColor,
        drawBorder: cfg.text.drawBorder,
        fillBackground: cfg.text.fillBackground,
        fixedSize: cfg.text.fixedSize,
        wordWrap: cfg.text.wordWrap,
        wordWrapWidth: cfg.text.wordWrapWidth,
        hAlign: cfg.text.hAlign,
        vAlign: cfg.text.vAlign,
      },
    });
  }

  if (key === 'rect' && p2 && p3) {
    shapes.push({
      kind: 'rectangle',
      p1: { time: p2.time, price: p2.price },
      p2: { time: p3.time + day, price: p3.price + (p3.price - p2.price) * 0.5 },
      style: {
        fillColor: cfg.rect.fillColor,
        borderColor: cfg.rect.borderColor,
        borderWidth: cfg.rect.borderWidth,
        transparency: cfg.rect.transparency,
      },
    });
  }

  if (key === 'ray' && p4) {
    shapes.push({
      kind: 'horizontal_ray',
      start: p4,
      direction: 'right',
      lengthSeconds: cfg.ray.lengthDays * day,
      style: {
        color: cfg.ray.color,
        width: cfg.ray.width,
        dashed: cfg.ray.dashed,
      },
      label: cfg.ray.labelText
        ? {
            text: cfg.ray.labelText,
            align: cfg.ray.labelAlign,
            vertical: cfg.ray.labelVertical,
            offsetPercent: (cfg.ray.labelOffsetPercent ?? 0.2) / 100,
            color: cfg.ray.labelColor,
            fontSize: cfg.ray.labelFontSize,
            hAlign: cfg.ray.labelHAlign,
            vAlign: cfg.ray.labelVAlign,
          }
        : undefined,
    });
  }

  if (key === 'arrow' && pMid) {
    shapes.push({
      kind: 'arrow',
      point: { time: pMid.time, price: pMid.price },
      direction: cfg.arrow.direction,
      style: {
        arrowColor: cfg.arrow.arrowColor,
        bold: cfg.arrow.bold,
        color: cfg.arrow.color,
        fontsize: cfg.arrow.fontsize,
        italic: cfg.arrow.italic,
        showLabel: cfg.arrow.showLabel,
      },
    });
  }

  if (key === 'triangle' && p2) {
    shapes.push({
      kind: 'triangle',
      point: { time: p2.time, price: p2.price },
      direction: cfg.triangle.direction,
      style: {
        backgroundColor: cfg.triangle.backgroundColor,
        color: cfg.triangle.color,
        fillBackground: cfg.triangle.fillBackground,
        linewidth: cfg.triangle.linewidth,
        transparency: cfg.triangle.transparency,
        sizePercent: cfg.triangle.sizePercent,
      },
    });
  }

  if (key === 'verticalLine' && p3) {
    shapes.push({
      kind: 'vertical_line',
      point: { time: p3.time, price: p3.price },
      style: {
        color: cfg.verticalLine.color,
        width: cfg.verticalLine.width,
        dashed: cfg.verticalLine.dashed,
        bold: cfg.verticalLine.bold,
        extendLine: cfg.verticalLine.extendLine,
        fontsize: cfg.verticalLine.fontsize,
        horzLabelsAlign: cfg.verticalLine.horzLabelsAlign,
        italic: cfg.verticalLine.italic,
        showTime: cfg.verticalLine.showTime,
        textcolor: cfg.verticalLine.textcolor,
        textOrientation: cfg.verticalLine.textOrientation,
        vertLabelsAlign: cfg.verticalLine.vertLabelsAlign,
      },
    });
  }

  if (key === 'horizontalLine' && p4) {
    shapes.push({
      kind: 'horizontal_line',
      point: { time: p4.time, price: p4.price },
      style: {
        linecolor: cfg.horizontalLine.linecolor,
        linewidth: cfg.horizontalLine.linewidth,
        linestyle: cfg.horizontalLine.linestyle,
        bold: cfg.horizontalLine.bold,
        showPrice: cfg.horizontalLine.showPrice,
        fontsize: cfg.horizontalLine.fontsize,
        textcolor: cfg.horizontalLine.textcolor,
        horzLabelsAlign: cfg.horizontalLine.horzLabelsAlign,
        vertLabelsAlign: cfg.horizontalLine.vertLabelsAlign,
        italic: cfg.horizontalLine.italic,
      },
    });
  }

  if (key === 'flag' && pMid) {
    shapes.push({
      kind: 'flag',
      point: { time: pMid.time, price: pMid.price },
      text: cfg.flag.content || '旗标',
      style: { flagColor: cfg.flag.flagColor },
    });
  }

  if (key === 'circle' && pMid) {
    const r = (cfg.circle.radiusPercent ?? 2) / 100 * pMid.price;
    shapes.push({
      kind: 'circle',
      center: { time: pMid.time, price: pMid.price },
      onCircle: { time: pMid.time, price: pMid.price + r },
      style: {
        backgroundColor: cfg.circle.backgroundColor,
        color: cfg.circle.color,
        fillBackground: cfg.circle.fillBackground,
        linewidth: cfg.circle.linewidth,
      },
    });
  }

  return shapes;
}

async function redraw() {
  const chart = widgetRef?.activeChart?.();
  if (!chart) return;
  clearChartShapes(chart, entityIds.value);
  entityIds.value = [];
  const shapes = buildShapes();
  const ids = await drawChartShapes(chart, shapes);
  entityIds.value = ids;
}

// 监听整个 cfg（deep），任意属性修改都触发重绘；nextTick 确保 v-model 已写回再重绘
watch(cfg, () => nextTick(redraw), { deep: true });
watch(activeShapeKey, () => nextTick(redraw));
</script>

<style scoped>
.shapes-demo input[type='color'] {
  padding: 0;
  border: 1px solid #363a45;
}
.shapes-demo input[type='number']::-webkit-inner-spin-button {
  opacity: 1;
}
</style>
