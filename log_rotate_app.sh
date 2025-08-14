#!/bin/bash

# =================================================================
# AIDocGenerator - app.log 专用日志轮转脚本
# 功能：轮转 logs/app.log 文件，确保始终有一个实时的 app.log 文件
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- 获取脚本所在目录 ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- 日志文件配置 ---
LOG_FILE="$DIR/logs/app.log"
MAX_SIZE="10M"  # 最大文件大小
BACKUP_COUNT=5  # 保留的备份文件数量

# --- 检查日志文件是否存在 ---
if [ ! -f "$LOG_FILE" ]; then
    echo -e "${YELLOW}⚠️  日志文件不存在: $LOG_FILE${NC}"
    echo -e "${BLUE}📝 创建新的日志文件...${NC}"
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    echo -e "${GREEN}✅ 已创建新的日志文件${NC}"
    exit 0
fi

# --- 获取当前文件大小 ---
CURRENT_SIZE=$(du -h "$LOG_FILE" | cut -f1)
echo -e "${BLUE}📊 当前日志文件大小: $CURRENT_SIZE${NC}"

# --- 检查是否需要轮转 ---
FILE_SIZE_BYTES=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
MAX_SIZE_BYTES=$(echo "$MAX_SIZE" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')

if [ "$FILE_SIZE_BYTES" -lt "$MAX_SIZE_BYTES" ]; then
    echo -e "${GREEN}✅ 日志文件大小正常，无需轮转${NC}"
    exit 0
fi

echo -e "${YELLOW}🔄 日志文件超过 $MAX_SIZE，开始轮转...${NC}"

# --- 轮转日志文件 ---
for i in $(seq $((BACKUP_COUNT-1)) -1 1); do
    if [ -f "${LOG_FILE}.$i" ]; then
        mv "${LOG_FILE}.$i" "${LOG_FILE}.$((i+1))"
    fi
done

# 备份当前日志文件
if [ -f "$LOG_FILE" ]; then
    mv "$LOG_FILE" "${LOG_FILE}.1"
    echo -e "${GREEN}✅ 已备份当前日志文件为 ${LOG_FILE}.1${NC}"
fi

# 创建新的空日志文件
touch "$LOG_FILE"
echo -e "${GREEN}✅ 已创建新的日志文件${NC}"

# --- 清理旧的备份文件 ---
for i in $(seq $((BACKUP_COUNT+1)) 10); do
    if [ -f "${LOG_FILE}.$i" ]; then
        rm -f "${LOG_FILE}.$i"
        echo -e "${YELLOW}🗑️  已删除旧备份文件: ${LOG_FILE}.$i${NC}"
    fi
done

echo -e "${GREEN}🎉 日志轮转完成！${NC}"
echo -e "${BLUE}📁 当前备份文件:${NC}"
ls -lh "${LOG_FILE}"*

# --- 显示文件大小信息 ---
echo ""
echo -e "${BLUE}📊 文件大小统计:${NC}"
for file in "${LOG_FILE}"*; do
    if [ -f "$file" ]; then
        size=$(du -h "$file" | cut -f1)
        echo -e "   - $(basename "$file"): $size"
    fi
done
