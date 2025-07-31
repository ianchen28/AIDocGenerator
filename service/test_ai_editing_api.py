#!/usr/bin/env python3
"""
AI 编辑 API 测试脚本
测试新创建的 AI 编辑工具和 API 端点
"""

import json
import requests
import time
from typing import Dict, Any

# API 基础配置
BASE_URL = "http://localhost:8000/api/v1"
EDIT_ENDPOINT = f"{BASE_URL}/actions/edit"

# 测试数据
TEST_TEXTS = {
    "polish": "这个文档写得不太好，有很多语法错误和表达不清的地方。",
    "expand": "人工智能在医疗领域的应用越来越广泛。",
    "summarize": """
    人工智能（AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。
    这些任务包括学习、推理、问题解决、感知和语言理解。AI 技术已经在各个领域得到广泛应用，
    包括医疗诊断、自动驾驶汽车、语音识别、自然语言处理和机器人技术。
    
    机器学习是 AI 的一个重要子领域，它使计算机能够在没有明确编程的情况下学习和改进。
    深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。
    
    AI 的发展经历了几个重要阶段，从早期的专家系统到现代的深度学习模型。
    近年来，大型语言模型的出现进一步推动了 AI 技术的发展。
    """
}

def test_health_check():
    """测试健康检查端点"""
    print("🔍 测试健康检查端点...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_edit_endpoint(action: str, text: str) -> Dict[str, Any]:
    """测试编辑端点"""
    print(f"\n🔍 测试 {action} 编辑功能...")
    print(f"原始文本: {text[:50]}{'...' if len(text) > 50 else ''}")
    
    payload = {
        "action": action,
        "text": text
    }
    
    try:
        response = requests.post(
            EDIT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {action} 编辑成功")
            print(f"编辑后文本: {result['edited_text'][:100]}{'...' if len(result['edited_text']) > 100 else ''}")
            return result
        else:
            print(f"❌ {action} 编辑失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return {"error": response.text}
            
    except requests.exceptions.Timeout:
        print(f"❌ {action} 编辑超时")
        return {"error": "请求超时"}
    except Exception as e:
        print(f"❌ {action} 编辑异常: {e}")
        return {"error": str(e)}

def test_invalid_requests():
    """测试无效请求"""
    print("\n🔍 测试无效请求...")
    
    # 测试无效的 action
    invalid_action_payload = {
        "action": "invalid_action",
        "text": "测试文本"
    }
    
    try:
        response = requests.post(EDIT_ENDPOINT, json=invalid_action_payload)
        if response.status_code == 400:
            print("✅ 无效 action 测试通过")
        else:
            print(f"❌ 无效 action 测试失败: {response.status_code}")
            print(f"响应内容: {response.text}")
    except Exception as e:
        print(f"❌ 无效 action 测试异常: {e}")
    
    # 测试空文本
    empty_text_payload = {
        "action": "polish",
        "text": ""
    }
    
    try:
        response = requests.post(EDIT_ENDPOINT, json=empty_text_payload)
        if response.status_code == 400:
            print("✅ 空文本测试通过")
        else:
            print(f"❌ 空文本测试失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 空文本测试异常: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试 AI 编辑 API 功能")
    print("=" * 50)
    
    # 1. 测试健康检查
    if not test_health_check():
        print("❌ 服务不可用，停止测试")
        return
    
    # 2. 测试各种编辑功能
    results = {}
    for action, text in TEST_TEXTS.items():
        result = test_edit_endpoint(action, text)
        results[action] = result
        time.sleep(1)  # 避免请求过于频繁
    
    # 3. 测试无效请求
    test_invalid_requests()
    
    # 4. 输出测试总结
    print("\n" + "=" * 50)
    print("📊 测试总结:")
    
    success_count = sum(1 for result in results.values() if "error" not in result)
    total_count = len(results)
    
    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("🎉 所有测试通过！AI 编辑功能正常工作")
    else:
        print("⚠️  部分测试失败，请检查服务配置")
    
    # 5. 保存测试结果
    with open("ai_editing_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("💾 测试结果已保存到 ai_editing_test_results.json")

if __name__ == "__main__":
    main() 