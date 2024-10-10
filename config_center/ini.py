import os
from errors import CcIniError

# 项目路径
config_center_path = os.path.dirname(os.path.abspath(__file__))
# 本文件中需要排除出去不放入snow的配置中心中的对象，包括函数、类、变量等，以globals()的输出结果为基准
self_black_list = ['os', 'CcIniError', 'config_center_path', 'get_ini', 'self_black_list', 'get_all_configs']


# 获取配置值
def get_ini(env_name: str, default_value: str | None):
    if os.getenv(env_name):
        return os.getenv(env_name)
    elif default_value:
        return default_value
    else:
        raise CcIniError(f'The env: {env_name} is not found.')


# 获取本文件中所有配置的键值
def get_all_configs() -> dict:
    r = {}
    for _k, _v in globals().items():
        if _k.startswith("__") and _k.endswith("__"):
            continue
        if _k in self_black_list:
            continue
        r[_k] = _v
    return r


# ============== Default Configs, No Modify ==============
# Docker 部署全部走环境变量获取配置，在 Dockerfile 中定义所有配置的默认值，docker-compose可自定义所有配置
# 本地运行全部走默认值获取配置
# API 服务端口
api_port = get_ini('API_PORT', '9791')
# 数据库节点
db_host = get_ini('DB_HOST', '10.45.186.149')
# 数据库端口
db_port = get_ini('DB_PORT', '9790')
# 数据库名称
db_name = get_ini('DB_NAME', 'cc')
# 数据库用户
db_user = get_ini('DB_USER', 'snow')
# 数据库密码
db_pass = get_ini('DB_PASS', 'snow@Sec123')
# cc 运行基路径
cc_work_path = get_ini('CC_WORK_PATH', './')
# 日志级别
log_level = get_ini('LOG_LEVEL', 'debug')
# snow 自身配置的 namespace 名称
snow_namespace = get_ini('SNOW_NAMESPACE', 'snow')
# 资源库基目录
resources_path = get_ini('RESOURCES_PATH', os.path.join(config_center_path, 'resources'))

# ============== 不暴露出去的默认配置 ==============
# 数据库连接参数
connect_args = {}

