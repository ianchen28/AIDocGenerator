#!/usr/bin/env python3
"""
自定义编辑命令测试脚本
"""

import json
import requests
import time
from typing import Dict, Any

# API 基础配置
BASE_URL = "http://localhost:8000/api/v1"
EDIT_ENDPOINT = f"{BASE_URL}/actions/edit"

# 测试数据
TEST_CASES = [{
    "name": "将文本改为正式语气",
    "action": "custom",
    "text": "这个项目做得不错，但是还有一些问题需要解决。",
    "command": "请将这段文本改为更正式的语气，使其适合商务场合。"
}, {
    "name": "将文本改为口语化",
    "action": "custom",
    "text": "本产品具有优异的性能和可靠的质量保证。",
    "command": "请将这段文本改为更口语化的表达，让普通用户更容易理解。"
}, {
    "name": "将文本翻译为英文",
    "action": "custom",
    "text": "人工智能技术正在改变我们的生活方式。",
    "command": "请将这段文本翻译为英文。"
}, {
    "name": "将文本改为诗歌风格",
    "action": "custom",
    "text": "春天来了，万物复苏。",
    "command": "请将这段文本改为诗歌风格，增加韵律感。"
}]


def test_custom_editing():
    """测试自定义编辑功能"""
    print("🚀 开始测试自定义编辑功能")
    print("=" * 50)

    results = {}

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n🔍 测试 {i}: {test_case['name']}")
        print(f"原始文本: {test_case['text']}")
        print(f"编辑指令: {test_case['command']}")

        payload = {
            "action": test_case["action"],
            "text": test_case["text"],
            "command": test_case["command"]
        }

        try:
            response = requests.post(
                EDIT_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 自定义编辑成功")
                print(f"编辑后文本: {result['edited_text']}")
                results[f"test_{i}"] = result
            else:
                print(f"❌ 自定义编辑失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                results[f"test_{i}"] = {"error": response.text}

        except Exception as e:
            print(f"❌ 自定义编辑异常: {e}")
            results[f"test_{i}"] = {"error": str(e)}

        time.sleep(1)  # 避免请求过于频繁

    # 输出测试总结
    print("\n" + "=" * 50)
    print("📊 自定义编辑测试总结:")

    success_count = sum(1 for result in results.values()
                        if "error" not in result)
    total_count = len(results)

    print(f"✅ 成功: {success_count}/{total_count}")
    print(f"❌ 失败: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("🎉 所有自定义编辑测试通过！")
    else:
        print("⚠️  部分自定义编辑测试失败")

    # 保存测试结果
    with open("custom_editing_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("💾 测试结果已保存到 custom_editing_test_results.json")


def test_validation():
    """测试验证功能"""
    print("\n🔍 测试验证功能...")

    # 测试缺少 command 参数
    payload = {
        "action": "custom",
        "text": "测试文本"
        # 故意不提供 command
    }

    try:
        response = requests.post(EDIT_ENDPOINT, json=payload)
        if response.status_code == 422:
            print("✅ 缺少 command 参数验证通过")
        else:
            print(f"❌ 缺少 command 参数验证失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证测试异常: {e}")


if __name__ == "__main__":
    test_custom_editing()
    test_validation()
