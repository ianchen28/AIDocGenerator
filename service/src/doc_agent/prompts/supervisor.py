# service/src/doc_agent/prompts/supervisor.py
"""
监督器提示词模板
"""

V1_DEFAULT = """**角色：** 你是一个高效的决策机器人。
**任务：** 根据下方的数据摘要，判断是否可以开始为「{topic}」撰写一个章节。

**决策标准：**
- 如果来源数量 >= 3 且总字符数 >= 200，返回 "FINISH"
- 如果来源数量 >= 2 且总字符数 >= 500，返回 "FINISH"
- 其他情况返回 "CONTINUE"

**数据摘要：**
- 来源数量: {num_sources}
- 总字符数: {total_length}

**你的决策：**
你的回答只能是一个单词："FINISH" 或 "CONTINUE"。
"""

V1_METADATA_BASED = """**角色：** 你是一个高效的决策机器人。
**任务：** 根据下方的数据摘要，判断是否可以开始为「{topic}」撰写一个章节。

**决策标准：**
- 如果来源数量 >= 3 且总字符数 >= 200，返回 "FINISH"
- 如果来源数量 >= 2 且总字符数 >= 500，返回 "FINISH"
- 其他情况返回 "CONTINUE"

**数据摘要：**
- 来源数量: {num_sources}
- 总字符数: {total_length}

**你的决策：**
你的回答只能是一个单词："FINISH" 或 "CONTINUE"。
"""

# 支持版本选择的PROMPTS字典
PROMPTS = {"v1_default": V1_DEFAULT, "v1_metadata_based": V1_METADATA_BASED}
