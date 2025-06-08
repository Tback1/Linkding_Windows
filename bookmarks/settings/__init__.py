# Use dev settings as default, use production if LD_ENV is production
import os

# 从环境变量 LD_ENV 获取当前环境，如果未设置则默认为 'development'
# 注意：这个变量名可以根据你的喜好修改
LD_ENV = os.getenv('LD_ENV', 'development')

if LD_ENV == 'production':
    from .prod import *
else:
    from .dev import *