#!/bin/bash

echo "🔍 Git 连接诊断工具"
echo "===================="

# 检查网络连接
echo "1. 检查网络连接..."
if ping -c 1 github.com > /dev/null 2>&1; then
    echo "   ✅ GitHub 网络连接正常"
else
    echo "   ❌ GitHub 网络连接失败"
fi

if ping -c 1 gitlab.com > /dev/null 2>&1; then
    echo "   ✅ GitLab 网络连接正常"
else
    echo "   ❌ GitLab 网络连接失败"
fi

# 检查SSH密钥
echo ""
echo "2. 检查SSH密钥..."
if [ -f ~/.ssh/id_rsa ] || [ -f ~/.ssh/id_ed25519 ]; then
    echo "   ✅ SSH密钥存在"
    ssh-add -l > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ SSH密钥已加载到代理"
    else
        echo "   ⚠️  SSH密钥未加载到代理"
    fi
else
    echo "   ❌ SSH密钥不存在"
fi

# 检查Git配置
echo ""
echo "3. 检查Git配置..."
echo "   用户名: $(git config --global user.name)"
echo "   邮箱: $(git config --global user.email)"
echo "   远程仓库: $(git remote get-url origin 2>/dev/null || echo '未设置')"

# 检查代理设置
echo ""
echo "4. 检查代理设置..."
HTTP_PROXY=$(git config --global --get http.proxy)
HTTPS_PROXY=$(git config --global --get https.proxy)

if [ -n "$HTTP_PROXY" ]; then
    echo "   HTTP代理: $HTTP_PROXY"
else
    echo "   HTTP代理: 未设置"
fi

if [ -n "$HTTPS_PROXY" ]; then
    echo "   HTTPS代理: $HTTPS_PROXY"
else
    echo "   HTTPS代理: 未设置"
fi

# 检查系统资源
echo ""
echo "5. 检查系统资源..."
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')

echo "   磁盘使用率: ${DISK_USAGE}%"
echo "   内存使用率: ${MEMORY_USAGE}%"

if [ "$DISK_USAGE" -gt 90 ]; then
    echo "   ⚠️  磁盘空间不足"
fi

if [ "$(echo "$MEMORY_USAGE > 90" | bc -l)" -eq 1 ]; then
    echo "   ⚠️  内存使用率过高"
fi

echo ""
echo "✅ 诊断完成！" 