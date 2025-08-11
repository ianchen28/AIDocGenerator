#!/usr/bin/env python3
"""
最小化测试
"""


def test_minimal():
    """最小化测试"""
    print("=== 开始最小化测试 ===")

    try:
        task_prompt = "请写一篇关于人工智能的文章，要求1000字"

        # 测试简单的 f-string
        prompt = f"用户输入: {task_prompt}"
        print("✅ 简单 f-string 测试成功")

        # 测试多行 f-string
        prompt2 = f"""
用户输入:
{task_prompt}
        """
        print("✅ 多行 f-string 测试成功")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"完整错误信息: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_minimal()
    if success:
        print("🎉 最小化测试通过！")
    else:
        print("❌ 最小化测试失败")
