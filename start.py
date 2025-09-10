import os
import sys
import logging
from dotenv import load_dotenv
from waitress import serve
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.core.exceptions import ImproperlyConfigured
from django.core.management import execute_from_command_line

# --- 1. 日志系统配置 ---
# 强制设置日志输出到控制台
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logging.root.setLevel(logging.DEBUG)  # 根 logger 设置为 DEBUG
logging.root.addHandler(console_handler)

logging.getLogger('django').setLevel(logging.INFO)  # Django 框架日志
logging.getLogger('bookmarks').setLevel(logging.DEBUG)  # Linkding 应用日志
logging.getLogger('waitress').setLevel(logging.DEBUG)  # 将 Waitress 内部日志级别设为 DEBUG
logging.getLogger('waitress.queue').setLevel(logging.DEBUG)  # 可能会有更多 Waitress 内部日志

logger = logging.getLogger('bookmarks_startup')
logger.info("--- Loggers configured for console output ---")

# --- 2. 脚本启动调试信息与环境检查 ---
logger.info("--- 脚本启动调试信息 ---")
script_dir = os.path.dirname(os.path.abspath(__file__))
current_working_dir = os.getcwd()

logger.info(f"脚本执行时的当前工作目录: {current_working_dir}")
logger.info(f"脚本文件本身路径 (__file__): {script_dir}")
logger.info(f"Python 解释器路径: {sys.executable}")

try:
    import waitress
    logger.info("Waitress 模块已加载。")
except ImportError:
    logger.error("Waitress 模块未找到，请确保已安装 (pip install waitress)。")
    sys.exit(1)

# --- 3. .env 文件加载 ---
env_path_option1 = os.path.join(script_dir, '.env')
env_path_option2 = os.path.join(os.path.dirname(script_dir), '.env')

if os.path.exists(env_path_option1):
    dotenv_path = env_path_option1
elif os.path.exists(env_path_option2):
    dotenv_path = env_path_option2
else:
    dotenv_path = None
    logger.warning("未找到 .env 文件。将尝试从系统环境变量加载。")

if dotenv_path:
    logger.info(f"计算出的 .env 文件路径: {dotenv_path}")
    if os.path.exists(dotenv_path):
        logger.info(f".env 文件在 {dotenv_path} 已找到。")
        load_dotenv_result = load_dotenv(dotenv_path, override=True)
        logger.info(f"load_dotenv 返回值: {load_dotenv_result}")
    else:
        logger.warning(f".env 文件 {dotenv_path} 不存在，无法加载。")
else:
    logger.warning("没有找到可用的 .env 文件路径。")

# --- 4. 设置项目根目录与 Python 路径 ---
BASE_DIR = script_dir
logger.info(f"Linkding 项目根目录: {BASE_DIR}")

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
    logger.info(f"已将 {BASE_DIR} 添加到 sys.path。")

if os.getcwd() != BASE_DIR:
    os.chdir(BASE_DIR)
    logger.info(f"已将当前工作目录切换到: {os.getcwd()}")

# --- 5. 设置代理环境变量 (如果存在) ---
http_proxy_env = os.getenv('HTTP_PROXY')
https_proxy_env = os.getenv('HTTPS_PROXY')
if http_proxy_env:
    os.environ['http_proxy'] = http_proxy_env
    logger.info(f"已设置环境变量 http_proxy: {http_proxy_env}")
if https_proxy_env:
    os.environ['https_proxy'] = https_proxy_env
    logger.info(f"已设置环境变量 https_proxy: {https_proxy_env}")
no_proxy_env = os.getenv('NO_PROXY')
if no_proxy_env:
    os.environ['no_proxy'] = no_proxy_env
    logger.info(f"已设置环境变量 no_proxy: {no_proxy_env}")

# --- 6. Django Settings Module 选择与核心 Django 设置 (预加载) ---
LD_ENV = os.getenv('LD_ENV', 'production')

if LD_ENV == 'production':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmarks.settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookmarks.settings.dev')

logger.info(f"DJANGO_SETTINGS_MODULE 已设置为: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

# 强制加载 settings 模块。
_ = settings.configured

# 现在，直接覆盖或添加设置到已加载的 settings 对象中
os.environ['DJANGO_DEBUG'] = 'False'
logger.info("已强制设置环境变量 DJANGO_DEBUG 为: False")
settings.DEBUG = False
logger.info(f"DEBUG: Django settings.DEBUG is now: {settings.DEBUG}")

# --- 您要修改的 Session 设置，现在直接赋值给 settings 对象 ---
settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = os.getenv('LD_SESSION_CONTRAL', 'true').lower() == 'true'
settings.SESSION_COOKIE_AGE = int(os.getenv('LD_SESSION_AGE', '3600'))
logger.info(f"SESSION_EXPIRE_AT_BROWSER_CLOSE: {settings.SESSION_EXPIRE_AT_BROWSER_CLOSE} (从 start.py 覆盖)")
logger.info(f"SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE} (从 start.py 覆盖)")

# --- 7. Nginx/HTTPS 代理相关 Django 设置 (集中放置) ---
settings.USE_X_FORWARDED_HOST = True
logger.info(f"USE_X_FORWARDED_HOST: {settings.USE_X_FORWARDED_HOST}")

settings.SECURE_HSTS_SECONDS = 31536000
settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
settings.SECURE_HSTS_PRELOAD = True
logger.info("HSTS (HTTP Strict Transport Security) 相关设置已应用。")

settings.SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
logger.info(f"SECURE_PROXY_SSL_HEADER: {settings.SECURE_PROXY_SSL_HEADER}")

settings.SECURE_SSL_REDIRECT = False
logger.info(f"SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT} (如果 Nginx 处理 HTTPS, 通常设为 False)")

# --- 8. ALLOWED_HOSTS 和 CSRF_TRUSTED_ORIGINS (关键安全配置) ---
_allowed_hosts_env = os.getenv("DJANGO_ALLOWED_HOSTS", "linkding.localhost,127.0.0.1,192.168.50.2,linkding.local:9095,192.168.50.2:9095")
settings.ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
logger.info(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")

_trusted_origins_from_env = os.getenv("LD_CSRF_TRUSTED_ORIGINS", "")
if _trusted_origins_from_env:
    settings.CSRF_TRUSTED_ORIGINS = [o.strip() for o in _trusted_origins_from_env.split(',') if o.strip()]
    logger.info(f"CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS} (从环境变量加载)")
else:
    settings.CSRF_TRUSTED_ORIGINS = [
        "https://linkding.localhost:9095",
        "https://linkding.local:9095",
        "https://192.168.50.2:9095",
        "https://127.0.0.1:9095",
    ]
    logger.info(f"CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS} (使用默认值)")

# --- 其他您希望通过 start.py 覆盖的设置也放在这里 ---
_secret_key_from_env = os.getenv("LD_SECRET_KEY")
if not _secret_key_from_env:
    logger.error("LD_SECRET_KEY 未在环境变量中设置！")
    sys.exit(1)
settings.SECRET_KEY = _secret_key_from_env
logger.info("DEBUG: settings.SECRET_KEY 已设置。")

settings.STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "bookmarks", "styles"),
    os.path.join(BASE_DIR, "bookmarks", "static"),
]
logger.info(f"DEBUG: Django settings.STATICFILES_DIRS set to: {settings.STATICFILES_DIRS}")

for d in settings.STATICFILES_DIRS:
    if not os.path.exists(d):
        logger.warning(f"警告: STATICFILES_DIRS 中的源目录不存在: {d}")
    else:
        logger.info(f"INFO: Source static files directory in STATICFILES_DIRS exists and is correct: {d}")

settings.STATIC_URL = "/" + os.getenv("LD_CONTEXT_PATH", "") + "static/"
logger.info(f"DEBUG: Django settings.STATIC_URL set to: {settings.STATIC_URL}")

settings.STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
logger.info(f"DEBUG: Django settings.STATICFILES_STORAGE set to: {settings.STATICFILES_STORAGE}")

settings.STATIC_ROOT = os.path.join(BASE_DIR, "static")
logger.info(f"DEBUG: Django settings.STATIC_ROOT set to: {settings.STATIC_ROOT}")
if not os.path.exists(settings.STATIC_ROOT):
    logger.warning(f"警告: STATIC_ROOT 目录不存在: {settings.STATIC_ROOT}。这可能导致静态文件无法加载。")
else:
    logger.info(f"INFO: STATIC_ROOT directory exists and is correct: {settings.STATIC_ROOT}")


# --- 9. Django 管理命令执行逻辑 ---
def run_management_command(command, *args):
    logger.info(f"正在执行 Django 管理命令: {command} {' '.join(args)}")

    # *** 新增的目录创建逻辑 ***
    if command == 'full_backup' and args:
        # 假设备份文件路径是 full_backup 命令的第一个参数
        backup_file_path = args[0]
        backup_dir = os.path.dirname(backup_file_path)
        if backup_dir and not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir, exist_ok=True)
                logger.info(f"已创建备份目录: {backup_dir}")
            except OSError as e:
                logger.error(f"无法创建备份目录 '{backup_dir}': {e}", exc_info=True)
                sys.exit(1)
    # *** 新增逻辑结束 ***

    original_sys_argv = sys.argv
    sys.argv = ['manage.py', command] + list(args)
    try:
        execute_from_command_line(sys.argv)
        logger.info(f"Django 管理命令 '{command}' 执行成功。")
    except Exception as e:
        logger.error(f"Django 管理命令 '{command}' 执行失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        sys.argv = original_sys_argv

if len(sys.argv) > 1 and sys.argv[1] == 'manage':
    run_management_command(*sys.argv[2:])
else:
    # --- 10. Waitress 服务器启动逻辑 ---
    logger.info("--- 启动 Waitress 服务器 ---")

    try:
        # 获取 Django WSGI 应用程序实例
        application = get_wsgi_application()
        logger.info("Django WSGI 应用程序加载成功。")

        # --- Django Request Logging Middleware ---
        class RequestLoggingMiddleware:
            def __init__(self, app):
                self.app = app
                self.logger = logging.getLogger('request_debugger')
                self.logger.setLevel(logging.DEBUG)

            def __call__(self, environ, start_response):
                self.logger.info("-" * 50)
                self.logger.info(f"Incoming Request Path: {environ.get('PATH_INFO')}")
                self.logger.info(f"Incoming Request URI: {environ.get('REQUEST_URI')}")
                self.logger.info(f"Incoming Request Full Path: {environ.get('RAW_URI')}")

                self.logger.info("--- Request Headers (environ) ---")
                for key, value in environ.items():
                    if key.startswith('HTTP_') or key in ['REMOTE_ADDR', 'SERVER_NAME', 'SERVER_PORT', 'REQUEST_METHOD', 'QUERY_STRING', 'wsgi.url_scheme']:
                        self.logger.info(f"  {key}: {value}")

                self.logger.info("--- Explicitly Check X-Forwarded Headers ---")
                self.logger.info(f"  X-Forwarded-Host: {environ.get('HTTP_X_FORWARDED_HOST', 'N/A')}")
                self.logger.info(f"  X-Forwarded-Proto: {environ.get('HTTP_X_FORWARDED_PROTO', 'N/A')}")
                self.logger.info(f"  X-Forwarded-For: {environ.get('HTTP_X_FORWARDED_FOR', 'N/A')}")
                self.logger.info(f"  Host (HTTP_HOST): {environ.get('HTTP_HOST', 'N/A')}")
                self.logger.info(f"  Scheme (wsgi.url_scheme): {environ.get('wsgi.url_scheme', 'N/A')}")
                self.logger.info("-" * 50)

                return self.app(environ, start_response)

        application = RequestLoggingMiddleware(application)
        logger.info("Request Logging Middleware applied.")

    except Exception as e:
        logger.error(f"加载 Django WSGI 应用程序失败: {e}", exc_info=True)
        sys.exit(1)

    logger.info("已通过 start.py 顶部部分应用自定义设置到 Django WSGI 应用程序。")

    if not settings.DEBUG:
        from whitenoise import WhiteNoise
        logger.info(f"DEBUG is False. Applying WhiteNoise to WSGI application, serving static files from {settings.STATIC_ROOT}")
        application = WhiteNoise(application, root=settings.STATIC_ROOT, prefix=settings.STATIC_URL)
    else:
        logger.info("DEBUG is True. WhiteNoise 将不会服务静态文件，Django 开发服务器会处理。")

    # Waitress 监听配置
    host = os.getenv("LD_HOST", "127.0.0.1")
    port = int(os.getenv("LD_PORT", 9090))
    threads = int(os.getenv("LD_THREADS", 4))

    logger.info("正在启动 Waitress 服务器，配置代理信任...")
    logger.info(f"Waitress 服务器即将开始监听在 http://{host}:{port}")

    try:
        serve(
            application,
            host=host,
            port=port,
            threads=threads,
            trusted_proxy=os.getenv("WAITRESS_TRUSTED_PROXY", "127.0.0.1"),
            trusted_proxy_headers={'x-forwarded-for', 'x-forwarded-host', 'x-forwarded-proto', 'x-forwarded-port'},
        )
    except Exception as e:
        logger.error(f"Waitress 服务器启动失败: {e}", exc_info=True)
        sys.exit(1)