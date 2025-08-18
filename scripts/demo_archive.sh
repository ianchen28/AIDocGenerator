#!/bin/bash

# 日志归档演示脚本
# 使用方法: ./demo_archive.sh

set -e

echo "📦 日志归档功能演示"
echo "=================================================="

# 创建演示目录
DEMO_DIR="demo_archive"
mkdir -p "$DEMO_DIR"
mkdir -p "$DEMO_DIR/logs"
mkdir -p "$DEMO_DIR/logs/archive"

echo "📁 创建演示目录: $DEMO_DIR"
echo ""

# 模拟日志轮转和归档
demo_archive_log() {
    local log_file="$1"
    local backup_count="$2"
    
    echo "🔍 演示归档过程: $log_file"
    
    # 创建一些备份文件
    echo "📝 创建备份文件..."
    for i in $(seq 1 8); do
        echo "备份内容 $i" > "${log_file}.$i"
        echo "   - 创建 ${log_file}.$i"
    done
    
    echo ""
    echo "📊 轮转前的文件状态:"
    ls -lh "${log_file}"*
    echo ""
    
    # 模拟轮转过程
    echo "🔄 开始轮转和归档..."
    
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
    
    # 步骤4: 归档过老的备份文件
    echo "   📦 步骤4: 归档过老的备份文件"
    for i in $(seq $((backup_count+1)) 10); do
        if [ -f "${log_file}.$i" ]; then
            # 创建archive目录
            local archive_dir="$DEMO_DIR/logs/archive/$(date '+%Y-%m')"
            mkdir -p "$archive_dir"
            
            # 移动文件到archive目录
            local archive_file="$archive_dir/$(basename "$log_file").$i"
            mv "${log_file}.$i" "$archive_file"
            echo "     - 归档: ${log_file}.$i → $archive_file"
        fi
    done
    
    echo ""
    echo "📊 轮转后的文件状态:"
    echo "   主日志目录:"
    ls -lh "${log_file}"*
    
    echo "   归档目录:"
    if [ -d "$DEMO_DIR/logs/archive" ]; then
        find "$DEMO_DIR/logs/archive" -type f -name "*.log.*" | while read -r file; do
            file_size=$(du -h "$file" | cut -f1)
            echo "   - $file ($file_size)"
        done
    fi
    
    echo ""
}

# 演示归档功能
echo "🔵 开始演示归档功能..."
echo ""

# 演示 worker_1.log 的归档
demo_archive_log "$DEMO_DIR/logs/worker_1.log" 5

echo "💡 归档功能总结:"
echo "   1. 轮转时保留最近5个备份文件 (.log.1 到 .log.5)"
echo "   2. 过老的备份文件 (.log.6 及以上) 会被移动到 archive/YYYY-MM/ 目录"
echo "   3. 主日志目录保持整洁，只保留活跃文件和最近备份"
echo "   4. 归档文件按月份组织，便于管理和查找"
echo ""

echo "🎯 归档优势:"
echo "   ✅ 主日志目录保持整洁"
echo "   ✅ 历史日志按月份归档，便于查找"
echo "   ✅ 自动清理过老的归档文件"
echo "   ✅ 保留重要的历史记录"
echo ""

# 清理演示文件
echo "🧹 清理演示文件..."
rm -rf "$DEMO_DIR"
echo "✅ 演示完成"
