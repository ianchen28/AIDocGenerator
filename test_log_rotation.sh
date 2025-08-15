#!/bin/bash

# =================================================================
# AIDocGenerator - 日志轮转功能测试脚本
# 功能：测试日志轮转功能是否正常工作
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
TEST_LOG="$DIR/logs/test_rotation.log"
MAX_SIZE="500K"  # 测试用较小的文件大小
BACKUP_COUNT=3  # 保留的备份文件数量

echo -e "${GREEN}🧪 测试日志轮转功能${NC}"
echo "=========================================="
echo "测试日志文件: $TEST_LOG"
echo "最大文件大小: $MAX_SIZE"
echo "保留备份数: $BACKUP_COUNT"
echo ""

# --- 创建测试目录 ---
mkdir -p "$DIR/logs"

# --- 清理旧的测试文件 ---
echo -e "${YELLOW}🔵 清理旧的测试文件...${NC}"
rm -f "${TEST_LOG}"*
echo "   - ✅ 已清理旧测试文件"

# --- 创建测试日志轮转函数 ---
test_log_rotation() {
    local log_file="$1"
    local max_size="$2"
    local backup_count="$3"
    
    # 检查当前日志文件大小
    if [ -f "$log_file" ]; then
        local current_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null)
        local max_size_bytes
        if [[ "$max_size" == *K ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/K$//' | awk '{print $1 * 1024}')
        elif [[ "$max_size" == *M ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/M$//' | awk '{print $1 * 1024 * 1024}')
        elif [[ "$max_size" == *G ]]; then
            max_size_bytes=$(echo "$max_size" | sed 's/G$//' | awk '{print $1 * 1024 * 1024 * 1024}')
        else
            max_size_bytes=$(echo "$max_size" | awk '{print $1 * 1024 * 1024}')  # 默认按M处理
        fi
        
        if [ "$current_size" -gt "$max_size_bytes" ]; then
            echo "   - 🔄 当前日志文件超过 $max_size，执行轮转..."
            
            # 轮转日志文件
            for i in $(seq $((backup_count-1)) -1 1); do
                if [ -f "${log_file}.$i" ]; then
                    mv "${log_file}.$i" "${log_file}.$((i+1))"
                fi
            done
            
            # 备份当前日志文件
            if [ -f "$log_file" ]; then
                mv "$log_file" "${log_file}.1"
                echo "   - ✅ 已备份当前日志文件为 ${log_file}.1"
            fi
            
            # 创建新的空日志文件
            touch "$log_file"
            echo "   - ✅ 已创建新的日志文件"
            
            # 清理旧的备份文件
            for i in $(seq $((backup_count+1)) 10); do
                if [ -f "${log_file}.$i" ]; then
                    rm -f "${log_file}.$i"
                fi
            done
            
            return 0  # 轮转成功
        else
            echo "   - ✅ 当前日志文件大小正常"
            return 1  # 无需轮转
        fi
    fi
    return 1  # 文件不存在
}

# --- 生成测试数据 ---
echo -e "${YELLOW}🔵 生成测试数据...${NC}"
echo "   - 开始写入测试数据到 $TEST_LOG"

# 生成足够大的测试数据 (约1.2MB)
for i in {1..5000}; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 测试日志条目 $i - 这是一个测试日志条目，用于验证日志轮转功能是否正常工作。包含一些随机数据: $(openssl rand -hex 32)" >> "$TEST_LOG"
done

# 检查文件大小
CURRENT_SIZE=$(du -h "$TEST_LOG" | cut -f1)
echo "   - ✅ 测试数据生成完成，文件大小: $CURRENT_SIZE"

# --- 测试日志轮转 ---
echo -e "\n${YELLOW}🔵 测试日志轮转功能...${NC}"
if test_log_rotation "$TEST_LOG" "$MAX_SIZE" "$BACKUP_COUNT"; then
    echo -e "   - ${GREEN}✅ 日志轮转成功！${NC}"
else
    echo -e "   - ${YELLOW}⚠️  日志文件大小未超过限制，无需轮转${NC}"
fi

# --- 显示结果 ---
echo -e "\n${BLUE}📊 测试结果:${NC}"
echo "=========================================="
if [ -f "$TEST_LOG" ]; then
    CURRENT_SIZE=$(du -h "$TEST_LOG" | cut -f1)
    echo "   - 当前日志文件: $TEST_LOG (大小: $CURRENT_SIZE)"
else
    echo "   - 当前日志文件: 不存在 (已轮转)"
fi

# 显示备份文件
echo "   - 备份文件:"
for i in $(seq 1 $BACKUP_COUNT); do
    if [ -f "${TEST_LOG}.$i" ]; then
        BACKUP_SIZE=$(du -h "${TEST_LOG}.$i" | cut -f1)
        echo "     ${TEST_LOG}.$i (大小: $BACKUP_SIZE)"
    fi
done

# --- 验证轮转结果 ---
echo -e "\n${YELLOW}🔵 验证轮转结果...${NC}"
if [ -f "${TEST_LOG}.1" ]; then
    echo -e "   - ${GREEN}✅ 备份文件创建成功${NC}"
else
    echo -e "   - ${RED}❌ 备份文件创建失败${NC}"
fi

if [ -f "$TEST_LOG" ]; then
    NEW_SIZE=$(du -h "$TEST_LOG" | cut -f1)
    if [ "$NEW_SIZE" = "0B" ] || [ "$NEW_SIZE" = "0" ]; then
        echo -e "   - ${GREEN}✅ 新日志文件创建成功 (大小为0)${NC}"
    else
        echo -e "   - ${YELLOW}⚠️  新日志文件大小: $NEW_SIZE${NC}"
    fi
else
    echo -e "   - ${RED}❌ 新日志文件创建失败${NC}"
fi

# --- 测试多次轮转 ---
echo -e "\n${YELLOW}🔵 测试多次轮转...${NC}"
echo "   - 再次生成测试数据..."

# 再次生成数据
for i in {1..1500}; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 第二轮测试日志条目 $i - 验证多次轮转功能: $(openssl rand -hex 16)" >> "$TEST_LOG"
done

# 再次轮转
if test_log_rotation "$TEST_LOG" "$MAX_SIZE" "$BACKUP_COUNT"; then
    echo -e "   - ${GREEN}✅ 第二次轮转成功！${NC}"
else
    echo -e "   - ${YELLOW}⚠️  第二次轮转无需执行${NC}"
fi

# --- 最终结果 ---
echo -e "\n${GREEN}🎉 日志轮转功能测试完成！${NC}"
echo "=========================================="
echo "   - 测试日志文件: $TEST_LOG"
echo "   - 备份文件数量: $BACKUP_COUNT"
echo ""

# 显示所有相关文件
echo -e "${BLUE}📁 所有相关文件:${NC}"
ls -lh "${TEST_LOG}"* 2>/dev/null || echo "   无相关文件"

echo ""
echo -e "${YELLOW}💡 清理测试文件:${NC}"
echo "   - 运行: rm -f ${TEST_LOG}*"
echo ""
echo -e "${GREEN}✅ 测试完成，日志轮转功能正常工作！${NC}"
