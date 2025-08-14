#!/bin/bash

# =================================================================
# AIDocGenerator - 日志轮转定时任务设置脚本
# 功能：设置 crontab 定时任务，自动轮转日志文件
# =================================================================

# --- 日志颜色 ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# --- 获取脚本所在目录 ---
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo -e "${GREEN}🚀 设置 AIDocGenerator 日志轮转定时任务${NC}"
echo "=========================================="

# --- 检查 log_rotate.sh 脚本是否存在 ---
if [ ! -f "$DIR/log_rotate.sh" ]; then
    echo -e "${RED}❌ 未找到 log_rotate.sh 脚本${NC}"
    exit 1
fi

# --- 获取当前用户的 crontab ---
CURRENT_CRONTAB=$(crontab -l 2>/dev/null || echo "")

# --- 检查是否已经存在日志轮转任务 ---
if echo "$CURRENT_CRONTAB" | grep -q "log_rotate.sh"; then
    echo -e "${YELLOW}⚠️  检测到已存在的日志轮转任务${NC}"
    echo ""
    read -p "是否要移除现有任务并重新设置? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 移除现有的日志轮转任务
        NEW_CRONTAB=$(echo "$CURRENT_CRONTAB" | grep -v "log_rotate.sh")
        echo "$NEW_CRONTAB" | crontab -
        echo -e "${GREEN}✅ 已移除现有日志轮转任务${NC}"
    else
        echo -e "${GREEN}保持现有任务不变。${NC}"
        exit 0
    fi
fi

# --- 选择轮转频率 ---
echo ""
echo -e "${BLUE}请选择日志轮转频率:${NC}"
echo "1) 每小时检查一次 (推荐)"
echo "2) 每天检查一次"
echo "3) 每周检查一次"
echo "4) 自定义"
echo ""
read -p "请选择 (1-4): " -n 1 -r
echo

case $REPLY in
    1)
        CRON_SCHEDULE="0 * * * *"  # 每小时
        SCHEDULE_DESC="每小时"
        ;;
    2)
        CRON_SCHEDULE="0 0 * * *"  # 每天午夜
        SCHEDULE_DESC="每天午夜"
        ;;
    3)
        CRON_SCHEDULE="0 0 * * 0"  # 每周日午夜
        SCHEDULE_DESC="每周日午夜"
        ;;
    4)
        echo ""
        echo -e "${BLUE}请输入自定义的 cron 表达式 (例如: 0 */6 * * * 表示每6小时):${NC}"
        read -p "Cron 表达式: " CRON_SCHEDULE
        SCHEDULE_DESC="自定义"
        ;;
    *)
        echo -e "${RED}❌ 无效选择，使用默认值 (每小时)${NC}"
        CRON_SCHEDULE="0 * * * *"
        SCHEDULE_DESC="每小时"
        ;;
esac

# --- 创建新的 crontab 条目 ---
NEW_CRON_ENTRY="$CRON_SCHEDULE $DIR/log_rotate.sh >> $DIR/logs/cron.log 2>&1"

# --- 添加到 crontab ---
if [ -z "$CURRENT_CRONTAB" ]; then
    echo "$NEW_CRON_ENTRY" | crontab -
else
    echo "$CURRENT_CRONTAB"$'\n'"$NEW_CRON_ENTRY" | crontab -
fi

echo ""
echo -e "${GREEN}🎉 日志轮转定时任务设置成功！${NC}"
echo "=========================================="
echo -e "   - ${BLUE}轮转频率:${NC} $SCHEDULE_DESC"
echo -e "   - ${BLUE}Cron 表达式:${NC} $CRON_SCHEDULE"
echo -e "   - ${BLUE}轮转脚本:${NC} $DIR/log_rotate.sh"
echo -e "   - ${BLUE}日志文件:${NC} $DIR/logs/app.log"
echo -e "   - ${BLUE}最大文件大小:${NC} 10M"
echo -e "   - ${BLUE}保留备份数:${NC} 5个"
echo ""

# --- 显示当前 crontab ---
echo -e "${BLUE}📋 当前 crontab 内容:${NC}"
crontab -l

echo ""
echo -e "${YELLOW}💡 管理命令:${NC}"
echo -e "   - 查看定时任务: crontab -l"
echo -e "   - 编辑定时任务: crontab -e"
echo -e "   - 移除定时任务: crontab -r"
echo -e "   - 手动轮转日志: $DIR/log_rotate.sh"
echo -e "   - 查看 cron 日志: tail -f $DIR/logs/cron.log"
echo ""
echo -e "${GREEN}✅ 日志轮转功能已启用，系统将自动管理日志文件大小${NC}"
