"""pytest 全局配置。

确保项目根目录在 sys.path 中，使得测试可以通过 `from automation import ...`
导入被测模块（无需安装为包）。
"""

import sys
from pathlib import Path

# 项目根目录 = tests/ 的上一级
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
