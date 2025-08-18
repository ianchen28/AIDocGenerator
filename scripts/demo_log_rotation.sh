#!/bin/bash

# 日志轮转演示脚本
# 使用方法: ./demo_log_rotation.sh

set -e

echo "🔄 日志轮转原理演示"
echo "=================================================="

# 创建演示目录
DEMO_DIR="demo_logs"
mkdir -p "$DEMO_DIR"

echo "📁 创建演示目录: $DEMO_DIR"
echo ""

# 模拟日志轮转函数
demo_rotate_log() {
    local log_file="$1"
    local max_size="$2"
    local backup_count="$3"
    
    echo "🔍 检查文件: $log_file"
    
    if [ ! -f "$log_file" ]; then
        echo "   ❌ 文件不存在"
        return
    fi
    
    # 获取文件大小
    local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
    local current_size_mb=$(echo "scale=2; $current_size / 1024 / 1024" | bc -l 2>/dev/null || echo "未知")
    
    # 转换最大大小到字节
    local max_size_bytes
    if [[ "$max_size" == *M ]]; then
        max_size_bytes=$(echo "$max_size" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')
    else
        max_size_bytes=$(echo "$max_size" | awk '{print $1 * 1024 * 1024}')  # 默认按M处理
    fi
    
    local max_size_mb=$(echo "scale=2; $max_size_bytes / 1024 / 1024" | bc -l 2>/dev/null || echo "未知")
    
    echo "   📊 当前大小: ${current_size_mb}MB, 限制: ${max_size_mb}MB"
    
    if [ "$current_size" -gt "$max_size_bytes" ]; then
        echo "   🔄 文件超过限制，开始轮转..."
        
        # 步骤1: 移动现有备份文件
        echo "   📦 步骤1: 移动现有备份文件"
        for i in $(seq $((backup_count-1)) -1 1); do
            if [ -f "${log_file}.$i" ]; then
                mv "${log_file}.$i" "${log_file}.$((i+1))"
                echo "     - ${log_file}.$i → ${log_file}.$((i+1))"
            fi
        done
        
        # 步骤2: 备份当前日志文件
        echo "   📦 步骤2: 备份当前日志文件"
        if [ -f "$log_file" ]; then
            mv "$log_file" "${log_file}.1"
            echo "     - $log_file → ${log_file}.1"
        fi
        
        # 步骤3: 创建新的空日志文件
        echo "   📦 步骤3: 创建新的空日志文件"
        touch "$log_file"
        echo "     - 创建新的 $log_file (0B)"
        
        # 步骤4: 清理旧备份
        echo "   📦 步骤4: 清理旧备份文件"
        for i in $(seq $((backup_count+1)) 10); do
            if [ -f "${log_file}.$i" ]; then
                rm -f "${log_file}.$i"
                echo "     - 删除 ${log_file}.$i"
            fi
        done
        
        echo "   ✅ 轮转完成"
    else
        echo "   ℹ️  文件大小正常，无需轮转"
    fi
    echo ""
}

# 创建演示文件
echo "📝 创建演示文件..."

# 创建一个超过限制的日志文件
echo "创建 worker_1.log (模拟超过10MB的文件)..."
dd if=/dev/zero of="$DEMO_DIR/worker_1.log" bs=1M count=12 2>/dev/null
echo "一些日志内容" >> "$DEMO_DIR/worker_1.log"

# 创建一些备份文件
echo "创建备份文件..."
echo "备份内容1" > "$DEMO_DIR/worker_1.log.1"
echo "备份内容2" > "$DEMO_DIR/worker_1.log.2"
echo "备份内容3" > "$DEMO_DIR/worker_1.log.3"

# 创建一个正常大小的文件
echo "创建 worker_2.log (正常大小)..."
echo "正常大小的日志内容" > "$DEMO_DIR/worker_2.log"

echo "✅ 演示文件创建完成"
echo ""

# 显示轮转前的状态
echo "📊 轮转前的文件状态:"
ls -lh "$DEMO_DIR"/
echo ""

# 演示轮转过程
echo "🔄 开始演示轮转过程..."
echo ""

# 轮转 worker_1.log (超过限制)
echo "1️⃣ 轮转 worker_1.log (超过10MB限制):"
demo_rotate_log "$DEMO_DIR/worker_1.log" "10M" 5

# 轮转 worker_2.log (正常大小)
echo "2️⃣ 轮转 worker_2.log (正常大小):"
demo_rotate_log "$DEMO_DIR/worker_2.log" "10M" 5

# 显示轮转后的状态
echo "📊 轮转后的文件状态:"
ls -lh "$DEMO_DIR"/
echo ""

# 演示写入过程
echo "📝 演示写入过程..."
echo "新的日志内容 $(date)" >> "$DEMO_DIR/worker_1.log"
echo "新的日志内容 $(date)" >> "$DEMO_DIR/worker_2.log"

echo "📊 写入后的文件状态:"
ls -lh "$DEMO_DIR"/
echo ""

echo "💡 轮转原理总结:"
echo "   1. 检测文件大小是否超过限制"
echo "   2. 如果超过，执行轮转操作："
echo "      - 移动现有备份: .log.1 → .log.2, .log.2 → .log.3, ..."
echo "      - 备份当前文件: .log → .log.1"
echo "      - 创建新文件: 新的空 .log 文件"
echo "   3. 继续写入新的 .log 文件"
echo "   4. 备份文件 (.log.1, .log.2, ...) 是只读的，用于历史查看"
echo ""

echo "🎯 关键点:"
echo "   ✅ 始终写入 .log 文件，不写入备份文件"
echo "   ✅ 轮转过程中服务不中断"
echo "   ✅ 备份文件保留历史记录"
echo "   ✅ 自动清理过旧的备份文件"
echo ""

# 清理演示文件
echo "🧹 清理演示文件..."
rm -rf "$DEMO_DIR"
echo "✅ 演示完成"
