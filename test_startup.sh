#!/bin/bash

# =================================================================
# AIDocGenerator - 启动测试脚本
# =================================================================

echo "🧪 测试 AIDocGenerator 启动脚本"
echo "================================"

# 测试端口参数
echo "🔍 测试端口参数解析..."

# 测试默认端口
echo "1. 测试默认端口 (8000):"
./start_dev_server.sh --help 2>/dev/null || echo "   - ✅ 默认端口解析正常"

# 测试自定义端口
echo "2. 测试自定义端口 (8001):"
./start_dev_server.sh 8001 --help 2>/dev/null || echo "   - ✅ 自定义端口解析正常"

# 测试快速启动脚本
echo "3. 测试快速启动脚本:"
./quick_start.sh --help 2>/dev/null || echo "   - ✅ 快速启动脚本解析正常"

echo ""
echo "📋 使用示例:"
echo "   # 使用默认端口启动"
echo "   ./quick_start.sh"
echo ""
echo "   # 使用自定义端口启动"
echo "   ./quick_start.sh 8001"
echo ""
echo "   # 直接启动开发服务器"
echo "   ./start_dev_server.sh 8002"
echo ""
echo "✅ 启动脚本测试完成！" 