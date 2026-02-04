#!/bin/bash
# 后端依赖安装脚本

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"

echo "项目根目录: $PROJECT_ROOT"
echo "虚拟环境路径: $VENV_PATH"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv "$VENV_PATH"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source "$VENV_PATH/bin/activate"

# 升级 pip
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo "安装后端依赖..."
cd "$(dirname "${BASH_SOURCE[0]}")"
pip install -r requirements.txt

echo "依赖安装完成！"
echo ""
echo "要启动服务，请运行："
echo "  source $VENV_PATH/bin/activate"
echo "  cd backend"
echo "  python run.py"
