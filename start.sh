#!/bin/bash

# AI Word Master - 启动脚本
# 用法: ./start.sh

echo "=========================================="
echo "  🚀 AI Word Master 启动程序"
echo "=========================================="
echo ""

# 进入项目目录
cd "$(dirname "$0")"

# 检查 Python 环境
if [ ! -f "/opt/anaconda3/envs/EAP/bin/python" ]; then
    echo "❌ 错误: 找不到 Python 环境 (EAP)"
    echo "   请确保 Anaconda 环境已安装"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
/opt/anaconda3/envs/EAP/bin/python -c "import flask, boto3, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    /opt/anaconda3/envs/EAP/bin/pip install -r requirements.txt -q
    echo "✓ 依赖安装完成"
fi

# 检查环境变量
echo "🔑 检查环境配置..."
if [ ! -f ".env" ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "   请创建 .env 文件并配置 API keys"
    exit 1
fi

# 检查 AWS 凭证
if [ ! -f "$HOME/.aws/credentials" ]; then
    echo "⚠️  警告: AWS 凭证未配置"
    echo "   请配置 ~/.aws/credentials 文件"
fi

# 清理旧进程
echo "🧹 清理旧进程..."
pkill -f "python.*server.py" 2>/dev/null
sleep 1

# 启动服务器
echo ""
echo "=========================================="
echo "  ✅ 启动服务器..."
echo "=========================================="
echo ""

/opt/anaconda3/envs/EAP/bin/python server.py
