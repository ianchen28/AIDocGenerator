# service/workers/tasks.py
# 假设使用 Celery
# from celery_app import app

# 修复相对导入
try:
    from ..core.container import container
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    import sys
    from pathlib import Path

    # 添加项目根目录到Python路径
    current_file = Path(__file__)
    service_dir = current_file.parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))

    from core.container import container


# @app.task
def run_generation_workflow(topic: str):
    """Celery任务: 运行文档生成图"""
    graph_input = {"topic": topic}

    # 从容器获取已编译并配置好依赖的图，然后执行
    # stream()方法可以流式返回每一步的结果，便于监控
    for step in container.graph.stream(graph_input):
        step_name = list(step.keys())[0]
        step_output = list(step.values())[0]

        # 在这里，你可以更新任务的状态到数据库或Redis
        print(f"Executing step: {step_name}")
        # update_task_progress(task_id, f"Finished step: {step_name}")

    final_result = step_output
    # save_final_document(task_id, final_result['final_document'])
    return "COMPLETED"
