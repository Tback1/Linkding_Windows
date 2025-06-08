#!/usr/bin/env python
import sys
import os

# --- START OF CUSTOM PATH FIX ---
# 获取 manage.py 所在的目录，即项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到 sys.path 的最前面
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 引入 dotenv 用于 migrate 时读取 .env 文件配置
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent # This manage.py's parent is the project root
dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmarks.settings.base') # 确保这行是正确的

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

# --- END OF CUSTOM PATH FIX ---

"""Django's command-line utility for administrative tasks."""

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookmarks.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
