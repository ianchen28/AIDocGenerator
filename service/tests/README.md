# 测试文件结构

本目录包含AIDocGenerator项目的所有测试文件，经过重新整理，结构更加清晰。

## 文件结构

### 综合测试文件

#### `test_es_comprehensive.py` - ES搜索综合测试

- **功能**: 全面的Elasticsearch搜索功能测试
- **包含测试**:
  - ES连接测试
  - 索引发现和映射分析
  - 基础文本搜索
  - 向量搜索
  - 工厂函数测试
  - 错误处理测试
  - 资源清理测试
- **运行方式**: `python tests/test_es_comprehensive.py`

#### `test_web_search_comprehensive.py` - Web搜索综合测试

- **功能**: 全面的Web搜索功能测试
- **包含测试**:
  - Web搜索工具创建
  - 基础搜索功能
  - 过滤搜索功能
  - 错误处理
  - 工厂函数测试
  - 配置集成测试
  - 性能测试
  - Agent集成测试
- **运行方式**: `python tests/test_web_search_comprehensive.py`

### 其他测试文件

#### `test_config.py` - 配置系统测试

- 测试配置加载和解析
- 环境变量处理
- YAML配置集成

#### `test_all_llm_clients.py` - LLM客户端综合测试

- 测试所有LLM客户端（OpenAI、Gemini、Reranker、Embedding等）
- 真实API调用测试
- 客户端配置和连接测试

#### `test_tools_factory.py` - 工具工厂测试

- 测试工具工厂函数
- 工具创建和管理
- 资源清理测试

## 运行测试

### 🚀 直接运行单个测试文件

现在所有测试文件都可以直接运行，无需额外配置：

```bash
# 直接运行任何测试文件
python tests/test_config.py
python tests/test_es_comprehensive.py
python tests/test_web_search_comprehensive.py
python tests/test_all_llm_clients.py
python tests/test_tools_factory.py
```

### 🎯 批量运行所有测试

```bash
# 运行所有测试
python tests/run_all_tests.py

# 运行特定测试
python tests/run_all_tests.py test_config
```

### 🔧 从service根目录运行

```bash
# 从service目录运行所有测试
python run_tests.py
```

### 📱 在Cursor/VS Code中运行

- 直接点击测试文件中的"运行"按钮
- 使用快捷键 `Ctrl+F5` (Windows/Linux) 或 `Cmd+F5` (Mac)
- 在终端中直接运行 `python 文件名.py`

## 测试特点

### 模块化设计

- 每个测试文件都是独立的，可以单独运行
- 测试类结构清晰，便于维护和扩展
- 统一的错误处理和结果报告

### 综合测试

- 合并了之前分散的测试文件
- 减少了重复代码
- 提高了测试覆盖率

### 独立运行

- 所有测试文件都可以独立运行
- 自动添加必要的路径配置
- 统一的日志配置
- 支持async with上下文管理器自动资源清理

## 测试结果

测试运行后会显示详细的测试结果，包括：

- 每个测试项的通过/失败状态
- 测试结果汇总
- 错误信息和调试信息

## 注意事项

1. **环境配置**: 确保已正确配置ES和Tavily等服务的连接信息
2. **依赖安装**: 确保已安装所有必要的Python包
3. **网络连接**: 部分测试需要网络连接（如Web搜索测试）
4. **权限**: 确保有足够的权限访问相关服务
5. **资源清理**: 测试会自动清理ES连接等资源，无需手动干预
6. **退出处理**: 已优化atexit注册，避免程序退出时的警告信息

## 扩展测试

如需添加新的测试，请遵循以下原则：

1. 使用类结构组织测试
2. 提供清晰的测试描述
3. 包含错误处理
4. 添加结果汇总
5. 保持代码风格一致
6. 使用async with进行资源管理
7. 继承TestBase类以获取通用功能

### 测试模板

```python
#!/usr/bin/env python3
"""
测试描述
"""

import sys
import os
import asyncio
from test_base import TestBase, setup_paths

# 设置路径
setup_paths()

class TestYourFeature(TestBase):
    """测试类"""
    
    @classmethod
    async def test_main(cls):
        """主测试方法"""
        cls.print_test_header("测试名称")
        
        # 测试逻辑
        try:
            # 你的测试代码
            pass
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
        
        cls.print_test_footer("测试名称", 1, 1)
        return True

if __name__ == "__main__":
    asyncio.run(TestYourFeature.test_main())
```
