#!/bin/bash

# =================================================================
# AIDocGenerator - Redis配置管理脚本
# =================================================================

CONFIG_FILE="service/src/doc_agent/core/config.yaml"

# 备份管理函数：只保留最近的两个备份
manage_backups() {
    local backup_dir=$(dirname "$CONFIG_FILE")
    local backup_pattern="${CONFIG_FILE}.backup.*"
    
    # 获取所有备份文件，按修改时间排序，保留最新的两个
    local backup_files=($(ls -t $backup_pattern 2>/dev/null))
    local total_backups=${#backup_files[@]}
    
    if [ $total_backups -gt 2 ]; then
        echo "🗑️  清理旧备份文件..."
        for ((i=2; i<total_backups; i++)); do
            rm -f "${backup_files[$i]}"
            echo "   删除: $(basename "${backup_files[$i]}")"
        done
        echo "✅ 已清理旧备份，保留最新的2个备份文件"
    fi
}

# 创建备份函数
create_backup() {
    local backup_file="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CONFIG_FILE" "$backup_file"
    echo "📋 已创建备份: $(basename "$backup_file")"
    manage_backups
}

echo "🔧 Redis配置管理"
echo "================"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    exit 1
fi

# 显示当前配置
echo "📋 当前Redis配置:"
if grep -A 20 "redis:" "$CONFIG_FILE" > /dev/null; then
    # 检查模式
    REDIS_MODE=$(grep -A 20 "redis:" "$CONFIG_FILE" | grep "mode:" | awk '{print $2}' | tr -d '"')
    echo "   - 模式: $REDIS_MODE"
    
    if [[ "$REDIS_MODE" == "cluster" ]]; then
        # 集群模式
        echo "   - 🌐 类型: Redis集群"
        CLUSTER_NODES=$(grep -A 20 "cluster:" "$CONFIG_FILE" | grep "nodes:" -A 10 | grep "-" | sed 's/.*- "\(.*\)"/\1/' | tr '\n' ' ')
        CLUSTER_PASSWORD=$(grep -A 20 "cluster:" "$CONFIG_FILE" | grep "password:" | awk '{print $2}' | tr -d '"')
        echo "   - 节点: $CLUSTER_NODES"
        echo "   - 密码: $CLUSTER_PASSWORD"
    else
        # 单节点模式
        echo "   - 🏠 类型: 单节点Redis"
        REDIS_HOST=$(grep -A 10 "single:" "$CONFIG_FILE" | grep "host:" | awk '{print $2}' | tr -d '"')
        REDIS_PORT=$(grep -A 10 "single:" "$CONFIG_FILE" | grep "port:" | awk '{print $2}')
        REDIS_DB=$(grep -A 10 "single:" "$CONFIG_FILE" | grep "db:" | awk '{print $2}')
        REDIS_PASSWORD=$(grep -A 10 "single:" "$CONFIG_FILE" | grep "password:" | awk '{print $2}' | tr -d '"')
        
        echo "   - 主机: $REDIS_HOST"
        echo "   - 端口: $REDIS_PORT"
        echo "   - 数据库: $REDIS_DB"
        echo "   - 密码: $REDIS_PASSWORD"
    fi
else
    echo "   - 未找到Redis配置"
fi

echo ""
echo "🔄 选择Redis配置:"
echo "   1. 本地Redis (127.0.0.1:6379)"
echo "   2. 远程Redis (10.215.149.74:26379)"
echo "   3. Redis集群 (6节点集群)"
echo "   4. 自定义单节点配置"
echo "   5. 自定义集群配置"
echo "   6. 测试当前配置"
echo "   7. 退出"

read -p "请选择 [1-7]: " choice

case $choice in
    1)
        echo "🔧 切换到本地Redis配置..."
        # 备份原配置
        create_backup
        
        # 更新为本地配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/mode:.*/mode: "single"/
        }' "$CONFIG_FILE"
        
        sed -i '' '/single:/,/^[^ ]/ {
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
        create_backup
        
        # 更新为远程配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/mode:.*/mode: "single"/
        }' "$CONFIG_FILE"
        
        sed -i '' '/single:/,/^[^ ]/ {
            s/host:.*/host: "10.215.149.74"/
            s/port:.*/port: 26379/
            s/db:.*/db: 0/
            s/password:.*/password: "xJrhp*4mnHxbBWN2grqq"/
        }' "$CONFIG_FILE"
        
        echo "✅ 已切换到远程Redis配置"
        ;;
    3)
        echo "🔧 切换到Redis集群配置..."
        # 备份原配置
        create_backup
        
        # 更新为集群配置
        cat > /tmp/redis_cluster_config.yaml << 'EOF'
  # 连接模式: "single" | "cluster"
  mode: "cluster"
  
  # 单节点配置 (mode: "single" 时使用)
  single:
    host: "127.0.0.1"
    port: 6379
    db: 0
    password: ""
  
  # 集群配置 (mode: "cluster" 时使用)
  cluster:
    nodes:
      - "10.215.149.74:6380"
      - "10.215.149.75:6380"
      - "10.215.149.76:6380"
      - "10.215.149.77:6380"
      - "10.215.149.78:6380"
      - "10.215.149.79:6380"
    max_redirects: 3
    password: "a20pNGJons"
    timeout: 35000
    
    # 连接池配置
    pool:
      max_active: 20
      max_idle: 10
      min_idle: 2
      max_wait: 5000
    
    # 集群刷新配置
    refresh:
      adaptive: true
      period: 30000
    
    # 关闭超时
    shutdown_timeout: 10000
    
    # 重试配置
    retry:
      attempts: 3
      interval: 5000
    
    # 并发配置
    concurrency: 1
EOF
        
        # 替换redis配置部分
        # 使用awk来安全地替换redis配置部分
        awk '
        BEGIN { in_redis = 0; printed = 0 }
        /^redis:/ { 
            in_redis = 1
            print "redis:"
            system("cat /tmp/redis_cluster_config.yaml")
            printed = 1
            next
        }
        /^[a-zA-Z]/ && in_redis { 
            in_redis = 0 
        }
        !in_redis { 
            print 
        }
        ' "$CONFIG_FILE" > /tmp/config_temp.yaml && mv /tmp/config_temp.yaml "$CONFIG_FILE"
        
        echo "✅ 已切换到Redis集群配置"
        ;;
    4)
        echo "🔧 自定义单节点Redis配置..."
        read -p "主机地址 [127.0.0.1]: " host
        host=${host:-127.0.0.1}
        
        read -p "端口 [6379]: " port
        port=${port:-6379}
        
        read -p "数据库 [0]: " db
        db=${db:-0}
        
        read -p "密码 (留空表示无密码): " password
        
        echo "🔧 更新配置..."
        # 备份原配置
        create_backup
        
        # 更新配置
        sed -i '' '/redis:/,/^[^ ]/ {
            s/mode:.*/mode: "single"/
        }' "$CONFIG_FILE"
        
        sed -i '' '/single:/,/^[^ ]/ {
            s/host:.*/host: "'"$host"'"/
            s/port:.*/port: '"$port"'/
            s/db:.*/db: '"$db"'/
            s/password:.*/password: "'"$password"'"/
        }' "$CONFIG_FILE"
        
        echo "✅ 已更新为自定义单节点配置"
        ;;
    5)
        echo "🔧 自定义Redis集群配置..."
        echo "请输入集群节点信息 (格式: host:port，每行一个，空行结束):"
        nodes=()
        while true; do
            read -p "节点 [host:port]: " node
            if [[ -z "$node" ]]; then
                break
            fi
            nodes+=("$node")
        done
        
        read -p "密码: " password
        password=${password:-""}
        
        read -p "最大重定向次数 [3]: " max_redirects
        max_redirects=${max_redirects:-3}
        
        read -p "超时时间(ms) [35000]: " timeout
        timeout=${timeout:-35000}
        
        echo "🔧 更新配置..."
        # 备份原配置
        create_backup
        
        # 创建临时配置文件
        cat > /tmp/custom_cluster_config.yaml << EOF
  # 连接模式: "single" | "cluster"
  mode: "cluster"
  
  # 单节点配置 (mode: "single" 时使用)
  single:
    host: "127.0.0.1"
    port: 6379
    db: 0
    password: ""
  
  # 集群配置 (mode: "cluster" 时使用)
  cluster:
    nodes:
EOF
        
        for node in "${nodes[@]}"; do
            echo "      - \"$node\"" >> /tmp/custom_cluster_config.yaml
        done
        
        cat >> /tmp/custom_cluster_config.yaml << EOF
    max_redirects: $max_redirects
    password: "$password"
    timeout: $timeout
    
    # 连接池配置
    pool:
      max_active: 20
      max_idle: 10
      min_idle: 2
      max_wait: 5000
    
    # 集群刷新配置
    refresh:
      adaptive: true
      period: 30000
    
    # 关闭超时
    shutdown_timeout: 10000
    
    # 重试配置
    retry:
      attempts: 3
      interval: 5000
    
    # 并发配置
    concurrency: 1
EOF
        
        # 替换redis配置部分
        sed -i '' '/redis:/,/^[^ ]/ {
            /redis:/,/^[^ ]/ {
                /redis:/!d
            }
        }' "$CONFIG_FILE"
        
        sed -i '' '/redis:/r /tmp/custom_cluster_config.yaml' "$CONFIG_FILE"
        rm /tmp/custom_cluster_config.yaml
        
        echo "✅ 已更新为自定义集群配置"
        ;;
    6)
        echo "🧪 测试当前Redis配置..."
        
        # 读取当前配置
        REDIS_CONFIG=$(python -c "
import sys
sys.path.append('service/src')
from doc_agent.core.config import settings
config = settings.redis_config
mode = config.get('mode', 'single')
if mode == 'cluster':
    cluster_config = config.get('cluster', {})
    nodes = cluster_config.get('nodes', [])
    password = cluster_config.get('password', '')
    if nodes:
        print(f'cluster:{nodes[0]}:{password}')
    else:
        print('cluster:127.0.0.1:6379:')
else:
    single_config = config.get('single', {})
    host = single_config.get('host', '127.0.0.1')
    port = single_config.get('port', 6379)
    password = single_config.get('password', '')
    print(f'single:{host}:{port}:{password}')
" 2>/dev/null)

        if [ $? -eq 0 ]; then
            IFS=':' read -r CONFIG_TYPE HOST PORT PASSWORD <<< "$REDIS_CONFIG"
            echo "   - 配置类型: $CONFIG_TYPE"
            echo "   - 测试连接: $HOST:$PORT"
            
            if [ -n "$PASSWORD" ]; then
                if redis-cli -h "$HOST" -p "$PORT" -a "$PASSWORD" ping > /dev/null 2>&1; then
                    echo "   - ✅ 连接成功"
                else
                    echo "   - ❌ 连接失败"
                fi
            else
                if redis-cli -h "$HOST" -p "$PORT" ping > /dev/null 2>&1; then
                    echo "   - ✅ 连接成功"
                else
                    echo "   - ❌ 连接失败"
                fi
            fi
        else
            echo "   - ❌ 无法读取配置"
        fi
        ;;
    7)
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