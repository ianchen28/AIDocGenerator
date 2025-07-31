#!/usr/bin/env python3
"""
AI 编辑器功能测试脚本
测试新的润色风格功能
"""

import asyncio
import json
import requests
from typing import AsyncGenerator

# 测试文本
TEST_TEXT = """
人工智能（AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。
这些任务包括学习、推理、问题解决、感知和语言理解。AI 技术已经在各个领域得到广泛应用，
从医疗诊断到自动驾驶汽车，从推荐系统到自然语言处理。
"""

async def test_ai_editor():
    """测试 AI 编辑器功能"""
    
    # 服务器地址
    base_url = "http://127.0.0.1:8000"
    
    # 测试不同的润色风格
    polish_styles = [
        "professional",
        "conversational", 
        "readable",
        "subtle",
        "academic",
        "literary"
    ]
    
    print("🧪 开始测试 AI 编辑器功能...")
    print("=" * 60)
    
    # 1. 测试健康检查
    print("1. 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        if response.status_code == 200:
            print("   ✅ 健康检查通过")
        else:
            print(f"   ❌ 健康检查失败: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ 无法连接到服务器: {e}")
        return
    
    # 2. 测试润色功能
    print("\n2. 测试润色功能...")
    for style in polish_styles:
        print(f"\n   📝 测试 {style} 风格润色...")
        
        # 构建请求数据
        request_data = {
            "action": "polish",
            "text": TEST_TEXT,
            "polish_style": style
        }
        
        try:
            # 发送流式请求
            response = requests.post(
                f"{base_url}/api/v1/actions/edit",
                json=request_data,
                stream=True,
                headers={"Accept": "text/event-stream"}
            )
            
            if response.status_code == 200:
                print(f"      ✅ {style} 风格请求成功")
                
                # 收集响应内容
                content = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]  # 移除 'data: ' 前缀
                            try:
                                data = json.loads(data_str)
                                if 'text' in data:
                                    content += data['text']
                                elif 'event' in data and data['event'] == 'end':
                                    break
                            except json.JSONDecodeError:
                                continue
                
                print(f"      📄 润色结果 (前100字符): {content[:100]}...")
                print(f"      📊 字符数: {len(content)}")
                
                # 验证流式输出的完整性
                if len(content) > 0:
                    print(f"      ✅ 流式输出正常，收到内容")
                else:
                    print(f"      ⚠️  流式输出异常，内容为空")
                
            else:
                print(f"      ❌ {style} 风格请求失败: {response.status_code}")
                print(f"      📄 错误信息: {response.text}")
                
        except Exception as e:
            print(f"      ❌ {style} 风格测试异常: {e}")
    
    # 3. 测试其他功能
    print("\n3. 测试其他编辑功能...")
    
    # 测试扩写功能
    print("\n   📝 测试扩写功能...")
    expand_data = {
        "action": "expand",
        "text": "AI 技术正在快速发展。"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/actions/edit",
            json=expand_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code == 200:
            print("      ✅ 扩写功能测试成功")
        else:
            print(f"      ❌ 扩写功能测试失败: {response.status_code}")
    except Exception as e:
        print(f"      ❌ 扩写功能测试异常: {e}")
    
    # 测试总结功能
    print("\n   📝 测试总结功能...")
    summarize_data = {
        "action": "summarize",
        "text": TEST_TEXT
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/actions/edit",
            json=summarize_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code == 200:
            print("      ✅ 总结功能测试成功")
        else:
            print(f"      ❌ 总结功能测试失败: {response.status_code}")
    except Exception as e:
        print(f"      ❌ 总结功能测试异常: {e}")
    
    # 4. 测试错误处理
    print("\n4. 测试错误处理...")
    
    # 测试无效的润色风格
    print("\n   📝 测试无效润色风格...")
    invalid_style_data = {
        "action": "polish",
        "text": TEST_TEXT,
        "polish_style": "invalid_style"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/actions/edit",
            json=invalid_style_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code == 200:
            print("      ⚠️  无效风格请求被接受（可能需要检查流式错误处理）")
        else:
            print(f"      ✅ 无效风格请求被正确拒绝: {response.status_code}")
    except Exception as e:
        print(f"      ❌ 无效风格测试异常: {e}")
    
    # 测试缺少润色风格参数
    print("\n   📝 测试缺少润色风格参数...")
    missing_style_data = {
        "action": "polish",
        "text": TEST_TEXT
        # 故意不包含 polish_style
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/actions/edit",
            json=missing_style_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code == 422:
            print("      ✅ 缺少风格参数请求被正确拒绝: 422 (验证错误)")
        elif response.status_code == 200:
            # 检查流式响应中是否有错误事件
            error_found = False
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if 'event' in data and data['event'] == 'error':
                                print(f"      ✅ 流式响应中正确返回错误: {data.get('detail', '未知错误')}")
                                error_found = True
                                break
                        except json.JSONDecodeError:
                            continue
            if not error_found:
                print("      ⚠️  缺少风格参数请求被接受且无错误处理")
        else:
            print(f"      ✅ 缺少风格参数请求被正确拒绝: {response.status_code}")
    except Exception as e:
        print(f"      ❌ 缺少风格参数测试异常: {e}")
    
    # 5. 测试流式输出实时性
    print("\n5. 测试流式输出实时性...")
    
    print("\n   📝 测试实时流式输出...")
    streaming_test_data = {
        "action": "polish",
        "text": "这是一个测试文本，用于验证流式输出的实时性。",
        "polish_style": "professional"
    }
    
    try:
        import time
        response = requests.post(
            f"{base_url}/api/v1/actions/edit",
            json=streaming_test_data,
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        if response.status_code == 200:
            print("      ✅ 流式请求成功，开始接收数据...")
            
            token_count = 0
            start_time = time.time()
            first_token_time = None
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                            if 'text' in data and data['text']:
                                token_count += 1
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    print(f"      📡 首个token到达时间: {first_token_time - start_time:.2f}秒")
                            elif 'event' in data and data['event'] == 'end':
                                end_time = time.time()
                                print(f"      📊 总共接收到 {token_count} 个token")
                                print(f"      ⏱️  总耗时: {end_time - start_time:.2f}秒")
                                print(f"      ✅ 流式输出测试完成")
                                break
                        except json.JSONDecodeError:
                            continue
        else:
            print(f"      ❌ 流式输出测试失败: {response.status_code}")
    except Exception as e:
        print(f"      ❌ 流式输出测试异常: {e}")

    print("\n" + "=" * 60)
    print("🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_ai_editor()) 