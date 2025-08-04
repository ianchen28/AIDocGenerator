#!/bin/bash

# 测试 curl 命令与 long 类型 sessionId 的兼容性

echo "🧪 测试 curl 命令与 long 类型 sessionId 的兼容性"
echo "=================================================="

# API 端点
API_URL="http://10.215.58.199:8000/api/v1/jobs/outline"

echo "📡 发送请求到: $API_URL"
echo "📋 请求数据包含 long 类型的 sessionId: 1951106983556190200"
echo ""

# 执行 curl 命令
curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "contextFiles": [
        {
            "updateDate": 1754018774000,
            "isContentRefer": null,
            "attachmentType": 0,
            "isStyleImitative": null,
            "isWritingRequirement": null,
            "sessionId": 1951106983556190200,
            "attachmentFileSize": 12341,
            "knowledgeId": 1917036801803659800,
            "deleteFlag": 0,
            "createBy": "zhang_hy5",
            "attachmentFileType": "docx",
            "updateBy": "zhang_hy5",
            "attachmentName": "表格内公式.docx",
            "id": 402,
            "knowledgeBaseId": 1910317878493385700,
            "attachmentFileToken": "eb31f7496636d42d2945254c4db91ae0",
            "attachmentSource": "上传大纲",
            "createDate": 1754018774000
        }
    ],
    "isOnline": false,
    "sessionId": 1951106983556190200,
    "taskPrompt": "生成一篇大纲"
}' \
  -w "\n\n📊 HTTP状态码: %{http_code}\n⏱️  响应时间: %{time_total}s\n" \
  --connect-timeout 10 \
  --max-time 30

echo ""
echo "🎉 测试完成!"
echo ""
echo "💡 如果看到 HTTP状态码: 202，说明 API 成功接受了 long 类型的 sessionId"
echo "💡 如果看到错误，请检查服务器是否正在运行" 