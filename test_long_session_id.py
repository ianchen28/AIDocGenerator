#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试long类型sessionId的兼容性
"""

import json
import requests
from pydantic import ValidationError

# 测试数据
test_data = {
    "contextFiles": [{
        "updateDate": 1754018774000,
        "isContentRefer": None,
        "attachmentType": 0,
        "isWritingRequirement": None,
        "isStyleImitative": None,
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
    1951106983556190200,  # long类型
    "taskPrompt":
    "生成一篇大纲"
}


def test_schema_validation():
    """测试Pydantic模型验证"""
    print("🔍 测试Pydantic模型验证...")

    try:
        from service.src.doc_agent.schemas import OutlineGenerationRequest

        # 测试long类型的sessionId
        request = OutlineGenerationRequest(**test_data)
        print(f"✅ 验证成功!")
        print(
            f"  session_id: {request.session_id} (类型: {type(request.session_id)})"
        )
        print(f"  task_prompt: {request.task_prompt}")
        print(f"  is_online: {request.is_online}")
        print(
            f"  context_files: {len(request.context_files) if request.context_files else 0} 个文件"
        )

        return True

    except ValidationError as e:
        print(f"❌ 验证失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def test_api_endpoint():
    """测试API端点"""
    print("\n🌐 测试API端点...")

    try:
        # 发送请求到API
        url = "http://localhost:8000/api/v1/jobs/outline"
        headers = {"Content-Type": "application/json"}

        print(f"发送请求到: {url}")
        print(f"请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")

        response = requests.post(url,
                                 json=test_data,
                                 headers=headers,
                                 timeout=10)

        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 202:
            print("✅ API端点测试成功!")
            return True
        else:
            print(f"❌ API端点测试失败，状态码: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器，请确保服务正在运行")
        return False
    except Exception as e:
        print(f"❌ API测试错误: {e}")
        return False


def test_curl_command():
    """生成curl命令"""
    print("\n📋 生成curl命令...")

    curl_command = f'''curl -X POST "http://localhost:8000/api/v1/jobs/outline" \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(test_data, ensure_ascii=False)}'
'''

    print("curl命令:")
    print(curl_command)

    # 保存到文件
    with open("test_curl_command.sh", "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\n")
        f.write("# 测试long类型sessionId的curl命令\n\n")
        f.write(curl_command)

    print("✅ curl命令已保存到 test_curl_command.sh")


def main():
    """主函数"""
    print("🚀 测试long类型sessionId兼容性")
    print("=" * 50)

    # 测试1: Pydantic模型验证
    schema_ok = test_schema_validation()

    # 测试2: API端点测试
    api_ok = test_api_endpoint()

    # 测试3: 生成curl命令
    test_curl_command()

    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  Pydantic模型验证: {'✅ 通过' if schema_ok else '❌ 失败'}")
    print(f"  API端点测试: {'✅ 通过' if api_ok else '❌ 失败'}")

    if schema_ok and api_ok:
        print("\n🎉 所有测试通过! long类型sessionId兼容性验证成功!")
    else:
        print("\n⚠️  部分测试失败，请检查相关配置")


if __name__ == "__main__":
    main()
