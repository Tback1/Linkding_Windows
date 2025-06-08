"""
WSGI config for linkding.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv # <-- 添加这行
from pathlib import Path       # <-- 添加这行

# 构建项目根目录的路径
BASE_DIR = Path(__file__).resolve().parent.parent # <-- 添加这行

# 加载 .env 文件中的环境变量
load_dotenv(os.path.join(BASE_DIR, '.env')) # <-- 添加这行

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookmarks.settings")

application = get_wsgi_application()