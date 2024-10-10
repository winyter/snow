from datetime import datetime
from typing import Union
import jinja2


class JinjaCustomizedFilters:
    @classmethod
    def add_filters(cls, jinja_env: jinja2.Environment):
        jinja_env.filters['ips_add_port'] = cls._ips_add_port
        jinja_env.filters['convert_time'] = cls._convert_time

    # IP、端口号拼接
    @staticmethod
    def _ips_add_port(
            ips: str,
            port: str,
            one_or_all: str
    ) -> str:
        # 如果IP或端口有空字符串，则直接返回空字符串，不执行拼接操作
        if not (ips and port):
            return ''
        if one_or_all == 'one':
            return list(map(
                    lambda x: '{0}:{1}'.format(x, port),
                    ips.split(',')
                ))[0]
        else:
            return ','.join(
                list(map(
                    lambda x: '{0}:{1}'.format(x, port),
                    ips.split(',')
                ))
            )

    @staticmethod
    def _convert_time(
            format_str: str,
            time_str: str = None,
            time_str_format: str = None
    ) -> Union[str, int]:
        """
        时间转换方法

        :param format_str: 输出的时间格式字符串，支持标准时间格式和"timestamp"字符串，如果传入 "timestamp"，则会以时间戳格式化
        :param time_str: 输入的时间，可为空，如果为空，方法会返回当前时间
        :param time_str_format: 输入的时间格式字符串，指定 time_str 的格式，用来给本方法解析。
            支持标准时间格式和"timestamp"字符串，如果传入 "timestamp"，则会以时间戳格式化。如果 time_str 为空，则此入参不需要传
        :return: 以 format_str 指定的格式输出的时间字符串(str)或时间戳(int)
        """

        def convert_to_timestamp(_time_str, _time_str_format):
            if _time_str_format == 'timestamp':
                return int(datetime.fromtimestamp(int(_time_str)).timestamp())
            elif _time_str_format:
                return int(datetime.strptime(_time_str, _time_str_format).timestamp())
            else:
                return _time_str

        def convert_to_format(_time_str, _time_str_format, _format_str):
            if _time_str_format == 'timestamp':
                return datetime.fromtimestamp(int(_time_str)).strftime(_format_str)
            elif _time_str_format:
                return datetime.strptime(_time_str, _time_str_format).strftime(_format_str)
            else:
                return _time_str

        if format_str == 'timestamp':
            if time_str is None:
                return int(datetime.now().timestamp())
            return convert_to_timestamp(time_str, time_str_format)
        else:
            if time_str is None:
                return datetime.now().strftime(format_str)
            return convert_to_format(time_str, time_str_format, format_str)


class JinjaHandler:
    _jinja_env = jinja2.Environment()
    JinjaCustomizedFilters.add_filters(_jinja_env)

    @classmethod
    def render(cls, row: str, **env) -> str:
        _template = cls._jinja_env.from_string(row)
        return _template.render(**env)

