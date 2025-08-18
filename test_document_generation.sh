#!/bin/bash

# 测试文档生成脚本
# 使用方法: ./test_document_generation.sh

echo "🧪 测试文档生成流程"
echo "=================================================="

# 调用文档生成API
echo "📡 调用文档生成API..."

curl -X POST "http://localhost:8081/api/v1/jobs/document-from-outline" \
  -H "Content-Type: application/json" \
  -d '{
    "outline": "ef9eff70e4dc524ec03d0f614517bda5",
    "isOnline": false,
    "sessionId": "test_session_$(date +%s)",
    "taskPrompt": "帮我写一篇关于信息检索技术的文章，篇幅大概在3000字左右"
  }' | jq '.'

echo ""
echo "⏳ 等待文档生成完成..."
echo "📊 监控日志输出..."

# 监控日志
echo "=================================================="
echo "🔄 实时日志监控 (按 Ctrl+C 停止):"
echo "=================================================="

# 监控所有相关日志
tail -f logs/app.log logs/worker_*.log 2>/dev/null | grep -E "(finalize_document|bibliography|completed_chapters|final_document|test\.md)" || echo "未找到相关日志"
