#!/usr/bin/env python3
"""
演示如何使用 Redis Stream 接收器
"""

import asyncio
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor


def run_receiver(job_id: str):
    """在后台运行接收器"""
    try:
        # 运行接收脚本
        process = subprocess.Popen(
            [sys.executable, "receive_stream_simple.py", job_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

        print(f"🎯 接收器已启动，监听任务: {job_id}")
        print("📝 实时内容将显示在下方:")
        print("=" * 60)

        # 实时显示输出
        while True:
            output = process.stdout.readline()
            if output:
                print(output.rstrip())
            else:
                # 检查进程是否还在运行
                if process.poll() is not None:
                    break
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 停止接收器")
        process.terminate()
    except Exception as e:
        print(f"❌ 接收器出错: {e}")
        process.terminate()


def run_writer_test(job_id: str):
    """运行 writer 测试"""
    try:
        print(f"🚀 启动 writer 测试，任务ID: {job_id}")

        # 修改测试脚本中的 job_id
        with open("test_stream_writer.py", "r", encoding="utf-8") as f:
            content = f.read()

        # 替换 job_id
        content = content.replace('job_id="test_job_001"',
                                  f'job_id="{job_id}"')

        with open("test_stream_writer_temp.py", "w", encoding="utf-8") as f:
            f.write(content)

        # 运行测试
        process = subprocess.run(
            [sys.executable, "test_stream_writer_temp.py"],
            capture_output=True,
            text=True)

        print("✅ Writer 测试完成")
        return process.returncode

    except Exception as e:
        print(f"❌ Writer 测试出错: {e}")
        return 1


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python demo_stream_receiver.py <job_id>")
        print("示例: python demo_stream_receiver.py demo_job_001")
        return

    job_id = sys.argv[1]

    print("🎬 开始演示 Redis Stream 接收器")
    print(f"📋 任务ID: {job_id}")
    print("=" * 60)

    # 使用线程池同时运行接收器和测试
    with ThreadPoolExecutor(max_workers=2) as executor:
        # 启动接收器
        receiver_future = executor.submit(run_receiver, job_id)

        # 等待一下让接收器启动
        time.sleep(2)

        # 启动 writer 测试
        test_future = executor.submit(run_writer_test, job_id)

        try:
            # 等待测试完成
            test_result = test_future.result()
            print(f"\n✅ 测试完成，返回码: {test_result}")

            # 等待一下让接收器处理完所有消息
            time.sleep(3)

        except KeyboardInterrupt:
            print("\n🛑 用户中断")
        finally:
            # 停止接收器
            receiver_future.cancel()

    # 清理临时文件
    try:
        import os
        if os.path.exists("test_stream_writer_temp.py"):
            os.remove("test_stream_writer_temp.py")
    except:
        pass

    print("🎉 演示完成")


if __name__ == "__main__":
    asyncio.run(main())
