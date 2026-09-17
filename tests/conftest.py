"""pytest 公共配置：让测试能直接 import 仓库根目录里的模块（本项目是扁平布局，非包）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
