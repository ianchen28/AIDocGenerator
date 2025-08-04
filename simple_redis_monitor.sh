#!/bin/bash

# =================================================================
# Redis 流持续监控脚本 (简化版)
# =================================================================

# Redis 配置
REDIS_HOST="10.215.149.74"
REDIS_PORT="26379"
REDIS_PASSWORD="xJrhp*4mnHxbBWN2grqq"

# 默认配置
JOB_ID="${1:-test_session_001}"
BLOCK_TIMEOUT=5000  # 5秒超时

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 优雅停止函数
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 正在停止监控...${NC}"
    echo -e "${GREEN}✅ 监控已停止${NC}"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 检查Redis连接
check_redis_connection() {
    echo -e "${BLUE}🔍 检查Redis连接...${NC}"
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis连接正常${NC}"
        return 0
    else
        echo -e "${RED}❌ Redis连接失败${NC}"
        return 1
    fi
}

# 显示帮助信息
show_help() {
    echo "🔍 Redis 流持续监控工具"
    echo "========================"
    echo ""
    echo "用法:"
    echo "  $0 [JOB_ID]"
    echo ""
    echo "参数:"
    echo "  JOB_ID    任务ID (默认: test_session_001)"
    echo ""
    echo "示例:"
    echo "  $0                    # 监控默认任务"
    echo "  $0 my_job_123        # 监控指定任务"
    echo ""
    echo "按 Ctrl+C 停止监控"
}

# 主函数
main() {
    # 检查帮助参数
    if [[ "$1" == "-h" || "$1" == "--help" ]]; then
        show_help
        exit 0
    fi
    
    echo -e "${BLUE}🚀 Redis 流持续监控工具${NC}"
    echo "=================================="
    echo -e "${BLUE}服务器:${NC} $REDIS_HOST:$REDIS_PORT"
    echo -e "${BLUE}任务ID:${NC} $JOB_ID"
    echo -e "${BLUE}流:${NC} job_events:$JOB_ID"
    echo -e "${BLUE}超时:${NC} ${BLOCK_TIMEOUT}ms"
    echo ""
    
    # 检查Redis连接
    if ! check_redis_connection; then
        exit 1
    fi
    
    # 检查流是否存在
    local stream_key="job_events:$JOB_ID"
    local stream_length=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" XLEN "$stream_key" 2>/dev/null)
    
    if [[ "$stream_length" == "0" || -z "$stream_length" ]]; then
        echo -e "${YELLOW}⚠️  流 $stream_key 不存在或为空${NC}"
        echo -e "${BLUE}💡 等待新消息...${NC}"
    else
        echo -e "${GREEN}📊 流长度: $stream_length${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}🔍 开始监控流: $stream_key${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止监控${NC}"
    echo ""
    
    # 开始监控
    local last_id="0"
    
    while true; do
        # 读取新消息
        local result=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --raw XREAD COUNT 10 BLOCK $BLOCK_TIMEOUT STREAMS "$stream_key" "$last_id" 2>/dev/null)
        
        if [[ -n "$result" ]]; then
            echo -e "${GREEN}📨 收到新消息:${NC}"
            echo "$result"
            echo ""
            
            # 更新最后读取的ID
            local new_id=$(echo "$result" | grep -o '[0-9]*-[0-9]*' | tail -1)
            if [[ -n "$new_id" ]]; then
                last_id="$new_id"
            fi
        fi
        
        # 显示心跳 (每30秒)
        local current_time=$(date '+%s')
        if [[ -z "$LAST_HEARTBEAT" ]]; then
            LAST_HEARTBEAT=0
        fi
        
        if [[ $((current_time - LAST_HEARTBEAT)) -ge 30 ]]; then
            echo -e "${YELLOW}💓 监控中... $(date '+%H:%M:%S')${NC}" >&2
            LAST_HEARTBEAT=$current_time
        fi
    done
}

# 运行主函数
main "$@" 