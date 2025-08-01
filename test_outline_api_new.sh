#!/bin/bash

# 测试 Outline 生成 API（新格式）
echo "测试 Outline 生成 API（驼峰格式）..."

# 基础测试（不带文件）
echo "1. 基础测试（不带文件）"
curl --location 'http://127.0.0.1:8000/api/v1/jobs/outline' \
--header 'Content-Type: application/json' \
--data '{
    "sessionId": "test-session-001",
    "taskPrompt": "生成一篇关于人工智能技术发展趋势的详细报告",
    "isOnline": true,
    "contextFiles": []
}'

echo -e "\n\n"

# 带文件测试
echo "2. 带文件测试"
curl --location 'http://127.0.0.1:8000/api/v1/jobs/outline' \
--header 'Content-Type: application/json' \
--data '{
    "sessionId": "test-session-002",
    "taskPrompt": "基于提供的文档，生成一份技术架构设计指南",
    "isOnline": false,
    "contextFiles": [
        {
            "updateDate": 1754018774000,
            "isContentRefer": 1,
            "attachmentType": 1,
            "isWritingRequirement": 1,
            "isStyleImitative": 1,
            "sessionId": 1951106983556190214,
            "attachmentFileSize": 12341,
            "knowledgeId": 1917036801803659703,
            "deleteFlag": 0,
            "createBy": "zhang_hy5",
            "attachmentFileType": "docx",
            "updateBy": "zhang_hy5",
            "attachmentName": "表格内公式.docx",
            "id": 402,
            "knowledgeBaseId": 1910317878493385715,
            "attachmentFileToken": "eb31f7496636d42d2945254c4db91ae0",
            "attachmentSource": "上传大纲",
            "createDate": 1754018774000
        }
    ]
}'

echo -e "\n\n测试完成！" 