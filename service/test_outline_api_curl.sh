#!/bin/bash

# =================================================================
# 大纲加载器API测试脚本
# =================================================================

echo "🧪 大纲加载器API测试"
echo "=================="

# 测试用的file_token（来自之前的测试）
FILE_TOKEN="2dbceb750506dc2f2bdc3cf991adab4d"

# API端点
API_URL="http://127.0.0.1:8000/api/v1/jobs/outline"

# 生成唯一的session_id
SESSION_ID=$(date +%s)

echo "📄 使用file_token: $FILE_TOKEN"
echo "🆔 Session ID: $SESSION_ID"
echo "🌐 API URL: $API_URL"
echo ""

# 构建请求JSON
REQUEST_JSON=$(cat <<EOF
{
  "sessionId": "$SESSION_ID",
  "taskPrompt": "请根据我上传的大纲文件生成一个标准格式的文档大纲",
  "isOnline": false,
  "contextFiles": [
    {
      "file_token": "$FILE_TOKEN",
      "file_name": "大纲示例.docx",
      "file_type": "docx"
    }
  ],
  "styleGuideContent": null,
  "requirements": "请保持原始大纲的结构和逻辑，确保章节层次清晰"
}
EOF
)

echo "📝 请求内容:"
echo "$REQUEST_JSON" | jq '.' 2>/dev/null || echo "$REQUEST_JSON"
echo ""

echo "🚀 发送请求..."
echo ""

# 发送curl请求
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "$REQUEST_JSON" \
  -w "\n\nHTTP状态码: %{http_code}\n响应时间: %{time_total}s\n" \
  -s

echo ""
echo "✅ 请求完成！"
echo ""
echo "📋 说明："
echo "   - 如果返回202状态码，说明任务已成功提交到后台"
echo "   - 可以通过返回的task_id查询任务进度"
echo "   - 任务完成后会生成标准格式的大纲JSON"
