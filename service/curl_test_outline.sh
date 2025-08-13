#!/bin/bash

# 简单的curl测试命令
curl -X POST "http://127.0.0.1:8000/api/v1/jobs/outline" \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "'$(date +%s)'",
    "taskPrompt": "请根据我上传的大纲文件生成一个标准格式的文档大纲",
    "isOnline": false,
    "contextFiles": [
      {
        "file_token": "2dbceb750506dc2f2bdc3cf991adab4d",
        "file_name": "大纲示例.docx",
        "file_type": "docx"
      }
    ],
    "styleGuideContent": null,
    "requirements": "请保持原始大纲的结构和逻辑，确保章节层次清晰"
  }'
