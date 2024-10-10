import os
import re
from typing import List, Dict, Tuple

import ini
from errors import CcTemplateNotFoundError, CcMetaIllegalError, CcResourcesError


# 元数据操作类
class ResourcesHandle:
    @classmethod
    def _analysis_data_content(cls, data_content: str, file_format: str) -> List[Dict]:
        """
        默认数据文件中第一行为表头
        :param data_content:
        :param file_format:
        :return:
        """
        format_directory = {
            'tsv': {
                'line_split': '\n',
                'column_split': '\t'
            }
        }
        # 读取文件格式化信息
        _format = format_directory[file_format]

        content_list = []
        # 切分输入字符串并过滤空白行
        for _ in data_content.split(_format['line_split']):
            if not re.search(r'^\s+$', _) and _:
                content_list.append(_)

        # 读取表头信息
        columns_list = content_list[0].strip('\n').strip(' ').strip('\r').split(_format['column_split'])
        # 读取并构建数据
        rows = []
        for line in content_list[1:]:
            row = line.strip('\n').strip(' ').strip('\r').split(_format['column_split'])
            _ = {}
            for _c_index in range(len(columns_list)):
                _[columns_list[_c_index]] = row[_c_index]
            rows.append(_)

        return rows

    # 获取库数据
    @classmethod
    def get_library_data(
            cls,
            namespace: str,
    ) -> Tuple[List[Dict], List[Dict], str]:
        resource_base_path = os.path.join(ini.resources_path, namespace)
        # 收集 resources 目录内容
        try:
            resource_file_list = os.listdir(resource_base_path)
        except FileNotFoundError:
            raise CcResourcesError(f'Resource path not found! namespace: {namespace}')
        _resources = {}
        for _ in resource_file_list:
            if os.path.isdir(os.path.join(resource_base_path, _)):
                _resources[_] = os.listdir(os.path.join(resource_base_path, _))
            else:
                with open(os.path.join(resource_base_path, _), mode='r', encoding='utf-8') as f:
                    _s = f.read()
                try:
                    _resources[_.split('.')[0]] = {'content': _s, 'format': _.split('.')[1]}
                except IndexError:
                    _resources[_.split('.')[0]] = {'content': _s, 'format': ''}

        # 读取 VERSION
        try:
            version = _resources['VERSION']['content']
        except KeyError:
            raise CcResourcesError(f"Resource file: [VERSION] not found.")

        # 读取 cc_configs_meta
        try:
            _ = _resources['cc_configs_meta']
        except KeyError:
            raise CcResourcesError(f"Resource file: [cc_configs_meta] not found.")
        _cc_configs_meta = cls._analysis_data_content(_['content'], _['format'])
        # 校验数据
        for _ in _cc_configs_meta:
            # 检查 level 字段值
            if _['level'] not in ['default', 'customized', 'default_overload']:
                raise CcMetaIllegalError(f'ERROR: The column value is illegal in meta data：{_}')

        # 读取 cc_templates_meta
        try:
            _ = _resources['cc_templates_meta']
        except KeyError:
            raise CcResourcesError(f"Resource file: [cc_templates_meta] not found.")
        try:
            _templates_list = _resources['templates']
        except KeyError:
            raise CcResourcesError(f"Resource path: [templates] not found.")
        _cc_templates_meta = cls._analysis_data_content(_['content'], _['format'])
        # 校验数据
        for _ in _cc_templates_meta:
            # 检查数据中的template文件是否真实存在
            if _['template_name'] not in _templates_list:
                raise CcTemplateNotFoundError(
                    f"Template file not found! namespace: {namespace}, template: {_}, template list: {_templates_list}")

        return _cc_configs_meta, _cc_templates_meta, version

    @classmethod
    def get_template_content(
            cls,
            namespace: str,
            template_name,
    ) -> str:
        _template_path = os.path.join(ini.resources_path, namespace, 'templates', template_name)
        # 检查模板是否存在
        try:
            _ = open(_template_path)
            _.close()
        except FileNotFoundError:
            raise CcTemplateNotFoundError

        # 读取
        with open(_template_path, mode='r', encoding='utf-8') as f:
            _ = f.read()

        return _
