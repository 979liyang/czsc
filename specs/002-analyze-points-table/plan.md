# Implementation Plan: 麒麟分析增加涨停跌停与买卖点时间节点表格

**Branch**: `002-analyze-points-table` | **Date**: 2025-03-01 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-analyze-points-table/spec.md`

## Summary

在麒麟分析链路中增加「涨停、跌停、第一/二/三类买点、第一/二/三类卖点」八类事件的时间节点数据：在 czsc 分析层按 K 线序列与笔/分型结果计算并产出事件列表（含时间节点），经后端序列化后由现有分析 API 返回，前端麒麟分析页以表格展示。时间节点粒度与当前分析周期一致（日/周/月为日期，分钟周期为日期+时间）。

## Technical Context

**Language/Version**: Python 3.x（czsc / backend）, TypeScript/Vue 3（frontend）  
**Primary Dependencies**: czsc（缠论分析）, FastAPI（backend）, Vue 3 + Pinia + Element Plus（frontend）  
**Storage**: 无新增持久化；分析结果由 API 即时计算返回  
**Testing**: pytest（czsc/backend）, 前端沿用现有测试方式  
**Target Platform**: 现有 Web 应用（后端 API + 前端麒麟分析页）  
**Project Type**: Web（backend + frontend 双端）  
**Performance Goals**: 单次分析响应与现有笔/分型计算同量级；新增事件列表为 O(n) 扫描，不显著增加耗时  
**Constraints**: 遵循项目编码规范（loguru、函数≤30 行、120 字符/行、中文注释）；不破坏现有分析 API 的请求/响应契约（仅扩展响应字段）  
**Scale/Scope**: 单次分析单周期；事件条数受 K 线数量与笔/分型数量约束，无需分页

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

项目 Constitution（`.specify/memory/constitution.md`）当前为占位模板，未定义强制门禁。开发遵循工作区规则：`.cursor/rules/czsc-coding-standards.mdc`（日志用 loguru、函数复杂度与格式、提交信息规范、中文注释）。无违规项，无需豁免。

## Project Structure

### Documentation (this feature)

```text
specs/002-analyze-points-table/
├── plan.md              # 本文件
├── research.md          # Phase 0 产出
├── data-model.md        # Phase 1 产出
├── quickstart.md        # Phase 1 产出
├── contracts/           # Phase 1 产出（API 契约）
└── tasks.md             # Phase 2 产出（/speckit.tasks，非本命令创建）
```

### Source Code (repository root)

```text
czsc/
├── analyze.py           # CZSC 类扩展：涨停/跌停/买卖点事件列表（属性或方法）
└── ...

backend/
├── src/
│   ├── models/serializers.py   # 新增事件列表序列化
│   ├── services/analysis_service.py  # 调用 czsc 新数据并写入 result
│   └── ...
└── tests/

frontend/
├── src/
│   ├── views/Analysis.vue      # 麒麟分析页：新增 8 类表格区域
│   ├── components/            # 可选：涨停/跌停/买卖点表格子组件
│   ├── api/analysis.ts        # 响应类型扩展
│   └── stores/analysis.ts     # 状态扩展（若需）
└── ...
```

**Structure Decision**: 沿用现有 Web 应用结构。数据在 czsc 层计算，backend 组装并序列化，frontend 仅展示与格式化时间；不新增服务或存储。

## Complexity Tracking

无宪法违规，无需填写。
