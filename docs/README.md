# 文档

## 项目文档索引

- **学习 CZSC / 因子与策略**：[learning/czsc_factors_and_strategies.md](learning/czsc_factors_and_strategies.md)
- **信号配置与因子库 / 数据库入库顺序**：[signals_and_factors.md](signals_and_factors.md)
- **信号函数学习**：[learning/czsc_signals.md](learning/czsc_signals.md)
- **信号分析与全盘扫描**：前端「信号分析」（/signal-analyze）仅信号、按类型添加、加号弹窗、默认半年前至今、可设每信号周期；「全盘扫描」（/screen）支持按信号或因子扫描全市场并查看结果（见 README 5. API 使用说明）。

## Sphinx 文档

pip install recommonmark sphinx_rtd_theme sphinx_automodapi
sphinx-quickstart

sphinx-apidoc.exe -o source ../czsc


在 base 环境下，执行以下命令，生成文档：

```shell
./make.bat clean
./make.bat html
```

## 参考资料

* [前复权、后复权、不复权价格区别与计算](https://liguoqinjim.cn/post/quant/fq_price/)
* [使用飞书创建自己的通知机器人](https://liguoqinjim.cn/post/tool/%E4%BD%BF%E7%94%A8%E9%A3%9E%E4%B9%A6%E5%88%9B%E5%BB%BA%E8%87%AA%E5%B7%B1%E7%9A%84%E9%80%9A%E7%9F%A5%E6%9C%BA%E5%99%A8%E4%BA%BA/)



