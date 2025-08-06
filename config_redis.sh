#!/bin/bash

# =================================================================
# AIDocGenerator - Redis配置管理脚本
# =================================================================

CONFIG_FILE="service/src/doc_agent/core/config.yaml"

echo "🔧 Redis配置管理"
echo "================"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 显示当前配置
echo "📋 当前Redis配置:"
if grep -A 4 "redis:" "$CONFIG_FILE" > /dev/null; then
    REDIS_HOST=$(grep -A 4 "redis:" "$CONFIG_FILE" | grep "host:" | awk '{print $2}' | tr -d '"')
    REDIS_PORT=$(grep -A 4 "redis:" "$CONFIG_FILE" | grep "port:" | awk '{print $2}')
    REDIS_DB=$(grep -A 4 "redis:" "$CONFIG_FILE" | grep "db:" | awk '{print $2}')
    REDIS_PASSWORD=$(grep -A 4 "redis:" "$CONFIG_FILE" | grep "password:" | awk '{print $2}' | tr -d '"')
    
    echo "   - 主机: $REDIS_HOST"
    echo "   - 端口: $REDIS_PORT"
    echo "   - 数据库: $REDIS_DB"
    echo "   - 密码: $REDIS_PASSWORD"
    
    # 显示配置类型
    if [[ "$REDIS_HOST" == "127.0.0.1" || "$REDIS_HOST" == "localhost" ]]; then
        echo "   - 🏠 类型: 本地Redis"
    else
        echo "   - 🌐 类型: 远程Redis"
    fi
else
    echo "   - 未找到Redis配置"
fi

echo ""
echo "🔄 选择Redis配置:"
echo "   1. 本地Redis (127.0.0.1:6379)"
echo "   2. 远程Redis (10.215.149.74:26379)"
echo "   3. 自定义配置"
echo "   4. 测试当前配置"
echo "   5. 退出"

read -p "请选择 [1-5]: " choice

case $choice in
    1)
        echo "🔧 切换到本地Redis配置..."
        # 备份原配置
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 更新为本地配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/host:.*/host: "127.0.0.1"/
            s/port:.*/port: 6379/
            s/db:.*/db: 0/
            s/password:.*/password: ""/
        }' "$CONFIG_FILE"
        
        echo "✅ 已切换到本地Redis配置"
        ;;
    2)
        echo "🔧 切换到远程Redis配置..."
        # 备份原配置
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 更新为远程配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/host:.*/host: "10.215.149.74"/
            s/port:.*/port: 26379/
            s/db:.*/db: 0/
            s/password:.*/password: "xJrhp*4mnHxbBWN2grqq"/
        }' "$CONFIG_FILE"
        
        echo "✅ 已切换到远程Redis配置"
        ;;
    3)
        echo "🔧 自定义Redis配置..."
        read -p "主机地址 [127.0.0.1]: " host
        host=${host:-127.0.0.1}
        
        read -p "端口 [6379]: " port
        port=${port:-6379}
        
        read -p "数据库 [0]: " db
        db=${db:-0}
        
        read -p "密码 (留空表示无密码): " password
        
        echo "🔧 更新配置..."
        # 备份原配置
        cp "$CONFIG_FILE" "${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 更新配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/host:.*/host: "'"$host"'"/
            s/port:.*/port: '"$port"'/
            s/db:.*/db: '"$db"'/
            s/password:.*/password: "'"$password"'"/
        }' "$CONFIG_FILE"
        
        echo "✅ 已更新为自定义配置"
        ;;
    4)
        echo "🧪 测试当前Redis配置..."
        
        # 读取当前配置
        REDIS_CONFIG=$(python -c "
import sys
sys.path.append('service/src')
from doc_agent.core.config import settings
config = settings.redis_config
print(f'{config[\"host\"]}:{config[\"port\"]}:{config.get(\"password\", \"\")}')
" 2>/dev/null)

        if [ $? -eq 0 ]; then
            IFS=':' read -r REDIS_HOST REDIS_PORT REDIS_PASSWORD <<< "$REDIS_CONFIG"
            echo "   - 测试连接: $REDIS_HOST:$REDIS_PORT"
            
            if [ -n "$REDIS_PASSWORD" ]; then
                if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
                    echo "   - ✅ 连接成功"
                else
                    echo "   - ❌ 连接失败"
                fi
            else
                if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
                    echo "   - ✅ 连接成功"
                else
                    echo "   - ❌ 连接失败"
                fi
            fi
        else
            echo "   - ❌ 无法读取配置"
        fi
        ;;
    5)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "📝 提示:"
echo "   - 重启服务以应用新配置: ./stop_dev_server.sh && ./quick_start.sh"
echo "   - 检查配置: ./check_status.sh"
echo "   - 恢复备份: 手动编辑 $CONFIG_FILE" 