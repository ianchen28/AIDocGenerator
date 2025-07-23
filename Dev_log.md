# 开发日志

## TODO

- [x] 各章的融合，以及文档结构的调整
- [ ] 实现API层，将这个强大的大脑暴露给外部世界。
- [ ] word 等文件的解析，ocr 调用返回内容的融入
- [ ] 代码，图，表，公式的渲染
- [ ] 不同模型的生成测试
- [ ] web 搜索的引入
- [ ] 无内容图片的生成（避免）

Week1 检查点


---

## 检查点: 2025-07-17 20:38 - 第3阶段结束

- **状态**: 成功组装和测试了整个 LangGraph 工作流使用 `_test_graph.py`。该代理展示了其全部能力：规划、研究、通过循环自我纠正和最终文档生成。
- **主要修改文件**: `@service/src/doc_agent/graph/builder.py`, `@_test_graph.py`
- **下一步**: 进入第3阶段：实现 API 层，将这个强大的大脑暴露给外部世界。

---

## 检查点: 2025-07-15 19:27 - 第2.2阶段结束

- **状态**: 成功组装和测试了整个 LangGraph 工作流使用 `_test_graph.py`。该代理展示了其全部能力：规划、研究、通过循环自我纠正和最终文档生成。
- **主要修改文件**: `@service/src/doc_agent/graph/builder.py`, `@_test_graph.py`
- **下一步**: 进入第3阶段：实现 API 层，将这个强大的大脑暴露给外部世界。

---

## 检查点: 2025-07-11 19:27 - 第2.1阶段结束

- **状态**: 在 `nodes.py` 中实现了 `planner_node`、`researcher_node` 和 `writer_node` 的初始逻辑。
- **主要修改文件**: `@service/src/doc_agent/graph/nodes.py`
- **下一步**: 在 `router.py` 中实现条件逻辑。

---

## 检查点: 2025-07-11 17:24 - 第1阶段结束

- **状态**: 完成了LLM客户端和工具的实现。`tests/` 中的所有单元测试都通过。
- **主要修改文件**:
  - `@service/src/doc_agent/llm_clients/base.py`
  - `@service/src/doc_agent/llm_clients/provider.py`
  - `@service/src/doc_agent/tools/web_search.py`
  - `@service/src/doc_agent/tools/es_search.py`
  - `@service/src/doc_agent/tools/es_discovery.py`
  - `@service/src/doc_agent/tools/es_service.py`
  - `@service/src/doc_agent/tools/code_execute.py`
- **下一步**: 在 `service/src/doc_agent/graph/nodes.py` 中实现图节点。
- **架构说明**: `researcher_node` 将负责将搜索结果聚合为单个字符串（目前阶段）。
