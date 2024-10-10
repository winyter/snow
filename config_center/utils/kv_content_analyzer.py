import re
from typing import Optional


# k=v 格式配置文件内容解析器
class KVFileContentAnalyzer:
    @staticmethod
    def parse(row: str) -> dict:
        config_content_list = row.strip('\n').split('\n')
        config_dict = {}
        config_re = r'^([a-z]|[A-Z]|\.|_|-|[0-9]|@)*=\S*'
        for cc in config_content_list:
            if re.search(config_re, cc):
                config_key = cc.split('=')[0]
                config_value = cc.split('=')[1]
            else:
                continue
            config_dict[config_key] = config_value
        return config_dict

    @staticmethod
    def unparse(
            parsed_data: dict,
            indent: int = 0,
            annotation_dict: Optional[dict] = None
    ) -> str:
        """
        :param parsed_data: 序列化的数据，字典格式
        :param indent: 等号两边的空隔，以空格符分隔，需要多少个空格在等号两边就传入对应的数字
        :param annotation_dict: 注释字典，本字典中的 key 与 serialized_data 中的 key 要统一
        :return:
        """
        _content = ''
        _indent_content = ' ' * indent
        for _key in parsed_data:
            try:
                _content += f'# {annotation_dict[_key]}\n{_key}{_indent_content}={_indent_content}{parsed_data[_key]}\n'
            except (KeyError, TypeError):
                _content += f'{_key}{_indent_content}={_indent_content}{parsed_data[_key]}\n'
        return _content
