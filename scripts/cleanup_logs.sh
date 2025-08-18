#!/bin/bash

# 日志清理脚本
# 使用方法: ./cleanup_logs.sh [保留天数]
# 示例: ./cleanup_logs.sh 30

set -e

LOG_DIR="../logs"
ARCHIVE_DIR="$LOG_DIR/archive"
DEFAULT_RETENTION_DAYS=30

# 获取保留天数
RETENTION_DAYS=${1:-$DEFAULT_RETENTION_DAYS}

echo "🧹 日志清理脚本"
echo "=================================================="
echo "日志目录: $LOG_DIR"
echo "归档目录: $ARCHIVE_DIR"
echo "保留天数: $RETENTION_DAYS 天"
echo ""

# 检查参数
if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]]; then
    echo "❌ 保留天数必须是整数"
    echo "使用方法: ./cleanup_logs.sh [保留天数]"
    echo "示例: ./cleanup_logs.sh 30"
    exit 1
fi

if [ "$RETENTION_DAYS" -lt 1 ]; then
    echo "❌ 保留天数必须大于0"
    exit 1
fi

echo "🔵 开始清理日志文件..."
echo ""

# 1. 清理过老的归档文件
echo "📦 清理过老的归档文件..."
if [ -d "$ARCHIVE_DIR" ]; then
    # 查找超过保留天数的归档文件
    old_files=$(find "$ARCHIVE_DIR" -type f -name "*.log.*" -mtime +$RETENTION_DAYS 2>/dev/null)
    
    if [ -n "$old_files" ]; then
        echo "   找到以下过老的文件:"
        echo "$old_files" | while read -r file; do
            file_size=$(du -h "$file" | cut -f1)
            file_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)
            echo "   - $file ($file_size, $file_date)"
        done
        
        echo ""
        echo "   🗑️  删除过老的归档文件..."
        find "$ARCHIVE_DIR" -type f -name "*.log.*" -mtime +$RETENTION_DAYS -delete 2>/dev/null
        echo "   ✅ 已删除过老的归档文件"
    else
        echo "   ℹ️  没有找到过老的归档文件"
    fi
    
    # 清理空的归档目录
    echo "   🗂️  清理空的归档目录..."
    find "$ARCHIVE_DIR" -type d -empty -delete 2>/dev/null
    echo "   ✅ 已清理空的归档目录"
else
    echo "   ℹ️  归档目录不存在: $ARCHIVE_DIR"
fi

echo ""

# 2. 清理过老的备份文件（在主日志目录中）
echo "📄 清理过老的备份文件..."
old_backup_files=$(find "$LOG_DIR" -maxdepth 1 -type f -name "*.log.*" -mtime +$RETENTION_DAYS 2>/dev/null)

if [ -n "$old_backup_files" ]; then
    echo "   找到以下过老的备份文件:"
    echo "$old_backup_files" | while read -r file; do
        file_size=$(du -h "$file" | cut -f1)
        file_date=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null)
        echo "   - $file ($file_size, $file_date)"
    done
    
    echo ""
    echo "   🗑️  删除过老的备份文件..."
    find "$LOG_DIR" -maxdepth 1 -type f -name "*.log.*" -mtime +$RETENTION_DAYS -delete 2>/dev/null
    echo "   ✅ 已删除过老的备份文件"
else
    echo "   ℹ️  没有找到过老的备份文件"
fi

echo ""

# 3. 显示清理后的状态
echo "📊 清理后的状态:"
echo "   主日志目录:"
ls -lh "$LOG_DIR"/*.log 2>/dev/null || echo "   无日志文件"

echo "   备份文件:"
ls -lh "$LOG_DIR"/*.log.* 2>/dev/null || echo "   无备份文件"

echo "   归档目录:"
if [ -d "$ARCHIVE_DIR" ]; then
    find "$ARCHIVE_DIR" -type f -name "*.log.*" | head -10 | while read -r file; do
        file_size=$(du -h "$file" | cut -f1)
        file_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$file" 2>/dev/null || stat -c "%y" "$file" 2>/dev/null | cut -d' ' -f1)
        echo "   - $file ($file_size, $file_date)"
    done
    
    total_archived=$(find "$ARCHIVE_DIR" -type f -name "*.log.*" | wc -l)
    if [ "$total_archived" -gt 10 ]; then
        echo "   ... 还有 $((total_archived - 10)) 个归档文件"
    fi
else
    echo "   无归档目录"
fi

echo ""
echo "💡 清理策略:"
echo "   - 保留最近 $RETENTION_DAYS 天的日志文件"
echo "   - 过老的文件会被移动到 archive/YYYY-MM/ 目录"
echo "   - 超过保留天数的归档文件会被删除"
echo "   - 空的归档目录会被自动清理"
echo ""
echo "💡 管理命令:"
echo "   - 查看归档文件: ls -lh $ARCHIVE_DIR/"
echo "   - 手动清理: ./cleanup_logs.sh $RETENTION_DAYS"
echo "   - 设置定时清理: 添加到 crontab"
echo ""

echo "✅ 日志清理完成"
