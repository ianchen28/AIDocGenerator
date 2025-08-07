#!/usr/bin/env python3
"""
测试二阶段文档生成 API 的脚本
测试 /jobs/document-from-outline 端点
"""

import asyncio
import json
import requests
import time
import sys
from pathlib import Path

# 添加项目路径 - 使用根目录的相对路径
sys.path.insert(0, str(Path(__file__).parent / "service" / "src"))

from loguru import logger

# 配置loguru输出到app.log文件和控制台
logger.remove()  # 移除默认处理器

# 添加控制台输出
logger.add(
    sys.stderr,
    level="DEBUG",
    format=
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
    colorize=True)

# 添加文件输出 - 使用根目录的相对路径
logger.add(
    "logs/app.log",
    level="DEBUG",
    format=
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    rotation="10 MB",
    retention="7 days",
    enqueue=False)  # 同步写入，确保实时输出


def test_document_generation_api():
    """测试文档生成 API"""

    # API 配置
    BASE_URL = "http://localhost:8000/api/v1"

    # 使用 outline_example.json 中的水电站主题大纲
    test_outline = {
        "title":
        "水电站建造过程中可能出现的问题与解决方案",
        "summary":
        "本报告主要探讨水电站建设过程中常见的问题，包括基坑开挖、混凝土浇筑、施工环境和技术要求等方面，并提出相应的解决方案。",
        "chapters": [{
            "number":
            1,
            "title":
            "水电站建设中的常见问题",
            "description":
            "本章详细分析水电站建设过程中常见的问题，包括基坑开挖、地下水处理和混凝土浇筑等方面的具体问题。",
            "sections": [{
                "number":
                1.1,
                "title":
                "基坑开挖中的问题",
                "description":
                "基坑开挖是水电站建设初期的关键步骤，本节讨论基坑开挖中常见的问题。",
                "key_points": ["基坑边坡坡比与设计不符", "戗台宽度与设计图纸不符", "存在大量超欠挖，需要二次开挖"]
            }, {
                "number":
                1.2,
                "title":
                "地下水处理问题",
                "description":
                "地下水丰富地区的混凝土浇筑面临特殊挑战，本节分析这些问题的具体表现。",
                "key_points":
                ["岩石裂隙水不能有效外排", "混凝土浇筑过程中水泥浆被冲走", "混凝土被水浸泡，造成蜂窝、麻面现象"]
            }, {
                "number":
                1.3,
                "title":
                "混凝土浇筑中的问题",
                "description":
                "混凝土浇筑是水电站建设中的重要环节，本节讨论混凝土浇筑中常见的问题。",
                "key_points": ["模板跑模、炸模、漏浆", "混凝土浇筑不均匀", "模板支撑不牢固导致混凝土变形"]
            }]
        }, {
            "number":
            2,
            "title":
            "水电站建设中的施工环境和技术要求",
            "description":
            "本章探讨水电站建设过程中面临的复杂施工环境和技术要求，以及相应的应对措施。",
            "sections": [{
                "number": 2.1,
                "title": "施工环境的复杂性",
                "description": "水电站一般建设在山区或河流陡坡地区，本节讨论施工环境的复杂性。",
                "key_points": ["工作场地狭小", "地形陡峭", "气候条件恶劣"]
            }, {
                "number": 2.2,
                "title": "施工技术要求",
                "description": "水电站建设涉及多个专业领域的技术，本节分析对施工人员的技术要求。",
                "key_points": ["水利水电工程专业技能", "电气工程专业技能", "机械工程专业技能"]
            }, {
                "number": 2.3,
                "title": "国际项目管理的特殊挑战",
                "description": "国际水电站项目面临额外的政治和环境因素，本节讨论这些特殊挑战。",
                "key_points": ["政治因素影响", "人员材料机械短缺", "生产组织的严峻挑战"]
            }]
        }],
        "total_chapters":
        2,
        "estimated_total_words":
        5000
    }

    # 准备请求数据
    request_data = {
        "jobId": f"test_job_{int(time.time())}",
        "sessionId": f"test_session_{int(time.time())}",
        "outlineJson": json.dumps(test_outline, ensure_ascii=False)
    }

    logger.info("🚀 开始测试文档生成 API")
    logger.info(f"📝 测试主题: {test_outline['title']}")
    logger.info(f"📋 章节数量: {len(test_outline['chapters'])}")
    logger.info(f"🆔 Session ID: {request_data['sessionId']}")

    try:
        # 发送请求
        url = f"{BASE_URL}/jobs/document-from-outline"
        logger.info(f"🌐 请求URL: {url}")

        response = requests.post(url,
                                 json=request_data,
                                 headers={"Content-Type": "application/json"},
                                 timeout=30)

        logger.info(f"📊 响应状态码: {response.status_code}")
        logger.info(f"📄 响应头: {dict(response.headers)}")

        if response.status_code == 202:
            response_data = response.json()
            logger.success("✅ 文档生成任务提交成功")
            logger.info(f"📄 完整响应: {response_data}")
            logger.info(f"🆔 Task ID: {response_data.get('redisStreamKey')}")
            logger.info(f"🆔 Session ID: {response_data.get('sessionId')}")

            # 返回任务ID用于后续监控
            return response_data.get('redisStreamKey')
        else:
            logger.error(f"❌ 请求失败: {response.status_code}")
            logger.error(f"📄 响应内容: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 网络请求失败: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return None


def monitor_task_progress(task_id: str, timeout: int = 300):
    """监控任务进度"""
    if not task_id:
        logger.error("❌ 没有有效的任务ID")
        return

    logger.info(f"🔍 开始监控任务进度: {task_id}")
    logger.info(f"⏱️  超时时间: {timeout} 秒")

    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            # 检查任务状态
            import redis
            r = redis.Redis(host='10.215.149.74',
                            port=26379,
                            password='xJrhp*4mnHxbBWN2grqq',
                            db=0)

            # 检查任务是否在Redis中
            task_exists = r.exists(task_id)
            if task_exists:
                try:
                    task_data = r.get(task_id)
                    logger.info(f"📊 任务数据: {task_data}")
                except redis.RedisError as e:
                    logger.warning(f"⚠️  无法读取任务数据: {e}")

            # 检查Celery任务状态
            try:
                celery_task_keys = r.keys('celery-task-meta-*')
                if celery_task_keys:
                    latest_task = celery_task_keys[-1]
                    latest_task_data = r.get(latest_task)
                    logger.info(f"📊 最新Celery任务: {latest_task}")
                    logger.info(f"📄 任务状态: {latest_task_data}")
            except redis.RedisError as e:
                logger.warning(f"⚠️  无法读取Celery任务状态: {e}")

            elapsed = int(time.time() - start_time)
            logger.info(f"⏳ 任务运行中... ({elapsed}s)")

        except KeyboardInterrupt:
            logger.info("⏹️  用户中断监控")
            break
        except Exception as e:
            logger.error(f"❌ 监控过程中出错: {e}")
            break

        time.sleep(5)

    logger.info("🏁 任务监控完成")


if __name__ == "__main__":
    # 测试文档生成 API
    task_id = test_document_generation_api()

    if task_id:
        # 监控任务进度
        monitor_task_progress(task_id)
    else:
        logger.error("❌ 无法获取任务ID，跳过监控")
