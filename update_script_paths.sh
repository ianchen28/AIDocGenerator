#!/bin/bash

# 批量更新脚本路径引用
# 使用方法: ./update_script_paths.sh

echo "🔧 更新脚本路径引用..."
echo "=================================================="

# 需要更新的脚本列表（除了quick_start_multi.sh，因为它在根目录运行）
scripts_to_update=(
    "scripts/stop_multi.sh"
    "scripts/watch_logs.sh"
    "scripts/log_rotate.sh"
    "scripts/cleanup_logs.sh"
    "scripts/demo_log_rotation.sh"
    "scripts/demo_archive.sh"
)

echo "📝 更新以下脚本的路径引用:"
for script in "${scripts_to_update[@]}"; do
    echo "   - $script"
done
echo ""

# 更新每个脚本
for script in "${scripts_to_update[@]}"; do
    if [ -f "$script" ]; then
        echo "🔧 更新 $script..."
        
        # 备份原文件
        cp "$script" "$script.bak"
        
        # 更新路径引用
        if [[ "$script" == *"monitor_all_workers.sh" ]]; then
            # monitor_all_workers.sh 已经在正确的路径
            echo "   ✅ 路径已正确"
        else
            # 其他脚本需要更新路径
            sed -i '' 's|LOG_DIR="logs"|LOG_DIR="../logs"|g' "$script"
            echo "   ✅ 已更新路径引用"
        fi
    else
        echo "   ❌ 文件不存在: $script"
    fi
done

echo ""
echo "✅ 路径更新完成"
echo ""
echo "💡 注意事项:"
echo "   - quick_start_multi.sh 在根目录运行，路径保持 logs/"
echo "   - 其他脚本在 scripts/ 目录运行，路径更新为 ../logs/"
echo "   - 原文件已备份为 .bak 文件"
