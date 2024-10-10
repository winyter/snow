import os
from typing import NoReturn
from sqlmodel import Session

import ini
from models import CcConfigs, CcTemplates, CcNamespaces, CcRegistryInfo
from crud import CrudCcConfigs, CrudCcTemplates, CrudCcNamespaces
from utils.resources_handler import ResourcesHandle
from utils.kv_content_analyzer import KVFileContentAnalyzer
from utils.jinja_handler import JinjaHandler
from utils.FileHandler import FileHandler
from errors import CcDataNotFoundError, CcMetaIllegalError


def execute_wizard(db_session: Session, namespace) -> str:
    # 载入数据
    _cc_configs_meta = ResourcesHandle.get_library_data(namespace)[0]
    try:
        _cc_configs = CrudCcConfigs.read_by_primary(db_session, namespace=namespace)
    except CcDataNotFoundError:
        _cc_configs = []

    # 比对 cc_configs 和 cc_configs_meta
    # 生成 cc_configs 表中所有配置键的列表，用来比对
    _cc_configs_key_list = []
    for _ in _cc_configs:
        _cc_configs_key_list.append(_.key)
    # 输出: 在meta但不在configs的配置项
    _in_meta_not_in_configs = []
    for _ in _cc_configs_meta:
        if _['key'] not in _cc_configs_key_list:
            _in_meta_not_in_configs.append(_)

    # 校验：如果没有配置变化，则返回空字符串
    _pre_rows = _in_meta_not_in_configs
    if not _pre_rows:
        return ''

    # 处理源数据
    _config_dict = {}
    _annotation_dict = {}
    for _ in _pre_rows:
        # 如果 meta 表中的 level 字段值为 customized，则将此配置放入向导配置中
        if _['level'] == 'customized':
            _config_dict[_['key']] = ''
            _annotation_dict[_['key']] = _['description']

    # 生成内容
    return KVFileContentAnalyzer.unparse(_config_dict, annotation_dict=_annotation_dict)


def registry(
        db_session: Session,
        data: CcRegistryInfo
) -> NoReturn:
    # 载入数据
    _wizard_configs = KVFileContentAnalyzer.parse(data.wizard_configs)
    _cc_configs_meta, _cc_templates_meta, _version = ResourcesHandle.get_library_data(data.namespace)
    try:
        _ = CrudCcConfigs.read_by_primary(db_session, namespace=data.namespace)
    except CcDataNotFoundError:
        _ = []

    # 将 cc_configs 数据转换为 key: value 字典，供下一步合并使用
    _cc_configs = {}
    for _c in _:
        _cc_configs[_c.key] = _c.value

    # 执行配置合并
    _result_configs = {}
    for _m in _cc_configs_meta:
        if _m['level'] == 'default_overload':
            _v = _m['value']
        elif _m['level'] == 'customized':
            try:
                _v = _wizard_configs[_m['key']]
            except KeyError:
                try:
                    _v = _cc_configs[_m['key']]
                except KeyError:
                    _v = _m['value']
        elif _m['level'] == 'default':
            try:
                _v = _cc_configs[_m['key']]
            except KeyError:
                _v = _m['value']
        else:
            raise CcMetaIllegalError(f'ERROR: 元数据中存在 level 字段值非法的数据：{_}')
        _result_configs[_m['key']] = CcConfigs(
            namespace=data.namespace,
            key=_m['key'],
            value=_v,
            description=_m['description'],
            category=_m['category']
        )

    # 生成项目配置环境变量，供渲染使用
    _center_configs = {}
    for _k, _v in _result_configs.items():
        _center_configs[_k] = _v.value

    # 生成snow配置环境变量，供渲染使用
    try:
        _snow_configs_raw = CrudCcConfigs.read_by_primary(db_session, namespace=ini.snow_namespace)
    except CcDataNotFoundError:
        _snow_configs_raw = []
    _snow_configs = {}
    for _scr in _snow_configs_raw:
        _snow_configs[_scr.key] = _scr.value

    # 拼合项目和snow的环境变量
    _render_envs = {
        'myself': _center_configs,
        'snow': _snow_configs
    }
    # 如果是snow的命名空间初始化，则去掉snow配置组，加入ini配置组
    if data.namespace == ini.snow_namespace:
        _render_envs = {
            'myself': _center_configs,
            'ini': ini.get_all_configs(),
        }

    # 写入cc_configs
    CrudCcConfigs.delete_all_namespace_rows(db_session, data.namespace)
    CrudCcConfigs.create(
        db_session,
        _result_configs.values(),
        **_render_envs
    )

    # 写入cc_templates
    CrudCcTemplates.delete_all_namespace_rows(db_session, data.namespace)
    for _ in _cc_templates_meta:
        CrudCcTemplates.create(
            db_session,
            [CcTemplates(
                namespace=data.namespace,
                template_name=_['template_name'],
                dest_address=_['dest_address'],
                dest_path=_['dest_path'],
                dest_user=_['dest_user'],
                dest_passwd=_['dest_passwd']
            )],
            **_render_envs
        )

    # 更新 cc_namespaces 表
    try:
        CrudCcNamespaces.update(db_session, data.namespace, version=_version)
    except CcDataNotFoundError:
        CrudCcNamespaces.create(db_session, CcNamespaces(namespace=data.namespace, version=_version))


def init_snow_configs(db: Session):
    with open(os.path.join(ini.resources_path, ini.snow_namespace, 'wizard.conf'),
              mode='r', encoding='utf-8') as f:
        _w = f.read()

    registry(db, CcRegistryInfo(namespace=ini.snow_namespace, wizard_configs=_w))


def deploy_template(
        db: Session,
        namespace: str,
        template_name: str
) -> NoReturn:
    # 读取模板及配置信息
    try:
        template_info = CrudCcTemplates.read_by_primary(db=db, namespace=namespace, template_name=template_name)[0]
        configs_info = CrudCcConfigs.read_by_primary(db=db, namespace=namespace)
        snow_configs_info = CrudCcConfigs.read_by_primary(db=db, namespace=ini.snow_namespace)
    except IndexError:
        raise CcDataNotFoundError

    # 读取模板内容
    _template_content = ResourcesHandle.get_template_content(namespace, template_name)

    # 生成中心配置，转换为key=value形式，提供渲染使用
    _center_configs = {
        'myself': {},
        'snow': {}
    }
    # 载入自身配置
    for _ in configs_info:
        _center_configs['myself'][_.key] = _.value
    # 载入snow配置
    for _ in snow_configs_info:
        _center_configs['snow'][_.key] = _.value

    # 渲染
    _rendered_template = JinjaHandler.render(_template_content, **_center_configs)

    # 发布
    _file_handle = FileHandler(
        file_path=template_info.dest_path,
        host=template_info.dest_address.split(':')[0],
        ssh_port=template_info.dest_address.split(':')[1],
        username=template_info.dest_user,
        password=template_info.dest_passwd
    )
    _file_handle.backup()
    _file_handle.write(_rendered_template)
