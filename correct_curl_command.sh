#!/bin/bash

# 正确的 curl 命令
curl --location 'http://127.0.0.1:8000/api/v1/actions/edit' \
--header 'Content-Type: application/json' \
--header 'Accept: text/event-stream' \
--data '{
    "action": "summarize",
    "text": "掌握React框架(组件化开发、状态管理)，能够独立完成项目搭建和部署，熟悉框架原理·掌握 HTML+CSS ，熟练掌握响应式布局 (媒体查询、弹性布局、网格布局)·掌握JavaScript，熟悉异步编程(Promise/Async/Await)、闭包、原型链等核心原理·掌握浏览器原理以及计算机网络相关技术，在性能优化方面有实践经验·有AI场景研发经验、大数据可视化项目经验，熟悉深度学习模型数据预处理流程和评估指标"
}' 