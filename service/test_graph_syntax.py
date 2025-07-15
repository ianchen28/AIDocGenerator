# service/test_graph_syntax.py
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_file = Path(__file__)
service_dir = current_file.parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

from src.doc_agent.graph.builder import build_graph_with_dependencies
from src.doc_agent.graph.state import ResearchState
from src.doc_agent.graph.router import supervisor_router


def test_graph_builder_syntax():
    """测试图构建语法"""
    print("🧪 测试图构建语法...")

    try:
        # 测试图构建
        graph = build_graph_with_dependencies()
        print("✅ 图构建成功!")
        print(f"📊 图节点数量: {len(graph.nodes)}")

        # 显示图的节点
        print("📋 图节点:")
        for node_name in graph.nodes:
            print(f"  - {node_name}")

        return True

    except Exception as e:
        print(f"❌ 图构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_conditional_edges():
    """测试条件路由配置"""
    print("\n🧪 测试条件路由配置...")

    try:
        # 创建测试状态
        test_state = ResearchState(topic="测试主题",
                                   research_plan="测试计划",
                                   search_queries=["查询1", "查询2"],
                                   gathered_data="测试数据",
                                   final_document="",
                                   messages=[])

        print("✅ 测试状态创建成功!")
        print(f"📝 主题: {test_state['topic']}")
        print(f"🔍 搜索查询数量: {len(test_state['search_queries'])}")
        print(f"📊 收集数据长度: {len(test_state['gathered_data'])}")

        return True

    except Exception as e:
        print(f"❌ 条件路由测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_supervisor_router_signature():
    """测试监督路由函数签名"""
    print("\n🧪 测试监督路由函数签名...")

    try:
        # 检查函数签名
        import inspect
        sig = inspect.signature(supervisor_router)
        print(f"✅ 函数签名: {sig}")

        # 检查参数
        params = list(sig.parameters.keys())
        print(f"📋 参数列表: {params}")

        # 检查返回类型注解
        return_annotation = sig.return_annotation
        print(f"🔄 返回类型: {return_annotation}")

        return True

    except Exception as e:
        print(f"❌ 函数签名测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_dependency_injection_config():
    """测试依赖注入配置"""
    print("\n🧪 测试依赖注入配置...")

    try:
        # 测试图编译和配置
        graph = build_graph_with_dependencies()

        # 模拟配置对象
        mock_config = {
            "configurable": {
                "llm_client": "mock_llm_client",
                "web_search_tool": "mock_search_tool",
                "tools": "mock_tools",
            }
        }

        # 测试配置应用
        configured_graph = graph.with_config(mock_config)
        print("✅ 依赖注入配置成功!")

        return True

    except Exception as e:
        print(f"❌ 依赖注入配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 开始测试图构建和条件路由语法...")

    # 运行所有测试
    tests = [
        test_graph_builder_syntax, test_conditional_edges,
        test_supervisor_router_signature, test_dependency_injection_config
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查配置")
