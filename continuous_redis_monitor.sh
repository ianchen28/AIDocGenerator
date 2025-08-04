#!/bin/bash

# =================================================================
# Redis 流持续监控脚本
# =================================================================

# Redis 配置
REDIS_HOST="10.215.149.74"
REDIS_PORT="26379"
REDIS_PASSWORD="xJrhp*4mnHxbBWN2grqq"

# 默认配置
DEFAULT_JOB_ID="test_session_001"
BLOCK_TIMEOUT=5000  # 5秒超时
MAX_COUNT=10        # 每次最多读取10条消息

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo "🔍 Redis 流持续监控工具"
    echo "========================"
    echo ""
    echo "用法:"
    echo "  $0 [选项] [JOB_ID]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -j, --job-id   指定任务ID (默认: $DEFAULT_JOB_ID)"
    echo "  -t, --timeout  设置阻塞超时时间(毫秒) (默认: $BLOCK_TIMEOUT)"
    echo "  -c, --count    设置每次读取的最大消息数 (默认: $MAX_COUNT)"
    echo "  -a, --all      监控所有流"
    echo "  -p, --pretty   使用美化输出格式"
    echo ""
    echo "示例:"
    echo "  $0                           # 监控默认任务"
    echo "  $0 my_job_123               # 监控指定任务"
    echo "  $0 -a                       # 监控所有流"
    echo "  $0 -p my_job_123           # 使用美化输出"
    echo "  $0 -t 10000 -c 20          # 设置10秒超时，每次读取20条"
    echo ""
    echo "按 Ctrl+C 停止监控"
}

# 解析命令行参数
JOB_ID="$DEFAULT_JOB_ID"
MONITOR_ALL=false
PRETTY_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -j|--job-id)
            JOB_ID="$2"
            shift 2
            ;;
        -t|--timeout)
            BLOCK_TIMEOUT="$2"
            shift 2
            ;;
        -c|--count)
            MAX_COUNT="$2"
            shift 2
            ;;
        -a|--all)
            MONITOR_ALL=true
            shift
            ;;
        -p|--pretty)
            PRETTY_OUTPUT=true
            shift
            ;;
        -*)
            echo "❌ 未知选项: $1"
            show_help
            exit 1
            ;;
        *)
            JOB_ID="$1"
            shift
            ;;
    esac
done

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

# 获取所有流
get_all_streams() {
    echo -e "${BLUE}📋 获取所有流...${NC}"
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --raw KEYS "job_events:*" | head -10
}

# 美化输出函数
pretty_print_message() {
    local stream_key="$1"
    local message_id="$2"
    local fields="$3"
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}📨 新消息${NC}"
    echo -e "${BLUE}流:${NC} $stream_key"
    echo -e "${BLUE}ID:${NC} $message_id"
    echo -e "${BLUE}时间:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # 解析字段
    while IFS= read -r line; do
        if [[ "$line" =~ ^[0-9]+$ ]]; then
            # 这是字段数量，跳过
            continue
        fi
        
        if [[ "$line" =~ ^[0-9]+$ ]]; then
            # 这是字段值长度，跳过
            continue
        fi
        
        # 处理字段名和值
        if [[ "$line" == "eventType" || "$line" == "event_type" ]]; then
            echo -e "${GREEN}事件类型:${NC} $line"
        elif [[ "$line" == "data" ]]; then
            echo -e "${GREEN}数据:${NC}"
            # 这里可以添加JSON解析逻辑
        else
            echo -e "${GREEN}$line${NC}"
        fi
    done <<< "$fields"
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 监控单个流
monitor_single_stream() {
    local stream_key="job_events:$JOB_ID"
    local last_id="0"
    
    echo -e "${BLUE}🔍 开始监控流: $stream_key${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止监控${NC}"
    echo ""
    
    while true; do
        # 读取新消息
        local result=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --raw XREAD COUNT $MAX_COUNT BLOCK $BLOCK_TIMEOUT STREAMS "$stream_key" "$last_id" 2>/dev/null)
        
        if [[ -n "$result" ]]; then
            # 解析结果
            while IFS= read -r line; do
                if [[ "$line" == "$stream_key" ]]; then
                    # 读取消息
                    read -r message_id
                    read -r field_count
                    
                    if [[ "$PRETTY_OUTPUT" == true ]]; then
                        pretty_print_message "$stream_key" "$message_id" "$field_count"
                    else
                        echo -e "${GREEN}📨 新消息: $message_id${NC}"
                        echo -e "${BLUE}字段数: $field_count${NC}"
                    fi
                    
                    last_id="$message_id"
                fi
            done <<< "$result"
        fi
        
        # 显示心跳
        echo -e "${YELLOW}💓 监控中... $(date '+%H:%M:%S')${NC}" >&2
    done
}

# 监控所有流
monitor_all_streams() {
    echo -e "${BLUE}🔍 开始监控所有流...${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止监控${NC}"
    echo ""
    
    # 获取所有流
    local streams=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --raw KEYS "job_events:*" 2>/dev/null)
    
    if [[ -z "$streams" ]]; then
        echo -e "${YELLOW}⚠️  没有找到任何流${NC}"
        return
    fi
    
    # 构建流参数
    local stream_params=""
    local id_params=""
    
    while IFS= read -r stream; do
        if [[ -n "$stream" ]]; then
            stream_params="$stream_params $stream"
            id_params="$id_params 0"
        fi
    done <<< "$streams"
    
    echo -e "${GREEN}📋 监控的流:${NC}"
    echo "$streams"
    echo ""
    
    while true; do
        # 读取所有流的新消息
        local result=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" --raw XREAD COUNT $MAX_COUNT BLOCK $BLOCK_TIMEOUT STREAMS $stream_params $id_params 2>/dev/null)
        
        if [[ -n "$result" ]]; then
            echo -e "${GREEN}📨 收到新消息:${NC}"
            echo "$result"
            echo ""
        fi
        
        # 显示心跳
        echo -e "${YELLOW}💓 监控中... $(date '+%H:%M:%S')${NC}" >&2
    done
}

# 主函数
main() {
    echo -e "${BLUE}🚀 Redis 流持续监控工具${NC}"
    echo "=================================="
    echo -e "${BLUE}服务器:${NC} $REDIS_HOST:$REDIS_PORT"
    echo -e "${BLUE}超时:${NC} ${BLOCK_TIMEOUT}ms"
    echo -e "${BLUE}最大消息数:${NC} $MAX_COUNT"
    
    if [[ "$MONITOR_ALL" == true ]]; then
        echo -e "${BLUE}模式:${NC} 监控所有流"
    else
        echo -e "${BLUE}任务ID:${NC} $JOB_ID"
        echo -e "${BLUE}流:${NC} job_events:$JOB_ID"
    fi
    
    if [[ "$PRETTY_OUTPUT" == true ]]; then
        echo -e "${BLUE}输出格式:${NC} 美化"
    fi
    
    echo ""
    
    # 检查Redis连接
    if ! check_redis_connection; then
        exit 1
    fi
    
    # 开始监控
    if [[ "$MONITOR_ALL" == true ]]; then
        monitor_all_streams
    else
        monitor_single_stream
    done
}

# 运行主函数
main 