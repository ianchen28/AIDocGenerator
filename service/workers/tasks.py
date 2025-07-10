# service/workers/tasks.py
# 假设使用 Celery
# from celery_app import app
from ..core.container import container


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
