#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 sessionId 兼容性修改
验证 API 是否能正确处理 long 类型的 sessionId
"""

import json
import requests
from typing import Union

# 测试数据
test_data = {
    "contextFiles": [{
        "updateDate": 1754018774000,
        "isContentRefer": None,
        "attachmentType": 0,
        "isStyleImitative": None,
        "isWritingRequirement": None,
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
    }],
    "isOnline":
    False,
    "sessionId":
    1951106983556190200,  # 这是一个 long 类型的 sessionId
    "taskPrompt":
    "生成一篇大纲"
}


def test_api_compatibility():
    """测试 API 兼容性"""
    print("🧪 测试 sessionId 兼容性")
    print("=" * 50)

    # API 端点
    api_url = "http://localhost:8000/api/v1/jobs/outline"

    try:
        print(f"📡 发送请求到: {api_url}")
        print(f"📋 请求数据:")
        print(
            f"  sessionId: {test_data['sessionId']} (类型: {type(test_data['sessionId'])})"
        )
        print(f"  taskPrompt: {test_data['taskPrompt']}")
        print(f"  isOnline: {test_data['isOnline']}")
        print(f"  contextFiles: {len(test_data['contextFiles'])} 个文件")

        # 发送请求
        response = requests.post(api_url,
                                 headers={"Content-Type": "application/json"},
                                 json=test_data,
                                 timeout=30)

        print(f"\n📊 响应状态码: {response.status_code}")

        if response.status_code == 202:
            response_data = response.json()
            print("✅ API 请求成功!")
            print(f"📋 响应数据:")
            print(f"  sessionId: {response_data.get('sessionId')}")
            print(f"  redisStreamKey: {response_data.get('redisStreamKey')}")
            print(f"  status: {response_data.get('status')}")
            print(f"  message: {response_data.get('message')}")

            # 验证 sessionId 类型兼容性
            session_id = response_data.get('sessionId')
            if isinstance(session_id, (int, str)):
                print(f"✅ sessionId 类型兼容性验证通过: {type(session_id)}")
            else:
                print(f"❌ sessionId 类型兼容性验证失败: {type(session_id)}")

        else:
            print(f"❌ API 请求失败")
            print(f"错误详情: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 API 服务器")
        print("💡 请确保服务器正在运行: python -m uvicorn api.main:app --reload")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")


def test_schema_validation():
    """测试 Pydantic 模型验证"""
    print("\n🔍 测试 Pydantic 模型验证")
    print("=" * 50)

    try:
        from service.src.doc_agent.schemas import OutlineGenerationRequest

        # 测试 long 类型的 sessionId
        request_data = {
            "sessionId": 1951106983556190200,
            "taskPrompt": "测试任务",
            "isOnline": False,
            "contextFiles": []
        }

        print(f"📋 测试数据:")
        print(
            f"  sessionId: {request_data['sessionId']} (类型: {type(request_data['sessionId'])})"
        )

        # 创建 Pydantic 模型实例
        request = OutlineGenerationRequest(**request_data)

        print(f"✅ Pydantic 模型验证成功!")
        print(
            f"  session_id: {request.session_id} (类型: {type(request.session_id)})"
        )
        print(f"  task_prompt: {request.task_prompt}")
        print(f"  is_online: {request.is_online}")

        # 测试字符串类型的 sessionId
        request_data_str = {
            "sessionId": "test_session_001",
            "taskPrompt": "测试任务",
            "isOnline": False,
            "contextFiles": []
        }

        print(f"\n📋 测试字符串类型 sessionId:")
        print(
            f"  sessionId: {request_data_str['sessionId']} (类型: {type(request_data_str['sessionId'])})"
        )

        request_str = OutlineGenerationRequest(**request_data_str)

        print(f"✅ 字符串类型 sessionId 验证成功!")
        print(
            f"  session_id: {request_str.session_id} (类型: {type(request_str.session_id)})"
        )

    except Exception as e:
        print(f"❌ Pydantic 模型验证失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试 sessionId 兼容性")
    print("=" * 60)

    # 测试 Pydantic 模型验证
    test_schema_validation()

    # 测试 API 兼容性
    test_api_compatibility()

    print("\n🎉 测试完成!")
