__all__ = [
    'FileHandler'
]

import os
from datetime import datetime

from utils.SSHConnectHandle import SSHConnectHandle


class NetFileHandle:
    def __init__(
            self,
            host: str,
            ssh_port: str,
            username: str,
            password: str,
            file_path: str
    ):
        self._ssh_handler = SSHConnectHandle(
            host=host,
            port=ssh_port,
            username=username,
            password=password
        )
        self._file_path = file_path

    def read(self):
        return self._ssh_handler.exec_command('cat {}'.format(self._file_path), is_return_stdout=True).rstrip()

    def write(self, data: str, is_overwrite: bool = True):
        if is_overwrite:
            return self._ssh_handler.exec_command('echo -e "{0}" > {1}'.format(data, self._file_path))
        else:
            return self._ssh_handler.exec_command('echo -e "{0}" >> {1}'.format(data, self._file_path))

    def copy(self, src: str, dst: str):
        return self._ssh_handler.exec_command('\\cp {} {}'.format(src, dst))

    def close(self):
        self._ssh_handler.close_connect()

    def delete(self):
        return self._ssh_handler.exec_command('rm -f {}'.format(self._file_path))


class FileHandler(NetFileHandle):
    """
    网络文件操作模块(使用基于 ssh 协议的 paramiko 模块实现)
    """
    def __init__(
            self,
            file_path: str,
            host: str,
            ssh_port: str,
            username: str,
            password: str,
    ):
        """
        :param file_path: 文件路径，绝对路径，必传参数
        :param host: 远程文件操作参数（基于ssh协议，仅支持Linux）, 目标文件所在节点IP
        :param ssh_port: 远程文件操作参数，ssh 协议端口
        :param username: 远程文件操作参数，文件所属用户
        :param password: 远程文件操作参数，文件所属用户的密码
        """
        super().__init__(host, ssh_port, username, password, file_path)

    def backup(self, backup_file_name: str | None = None):
        """
        :param backup_file_name: 自定义备份文件名，默认文件名为：.[source_file_name].[%Y%m%d%H%M%S].bak
        :return:
        """
        _bf_name = '.{0}.{1}.snow'.format(os.path.basename(self._file_path), datetime.now().strftime("%Y%m%d%H%M%S"))
        if backup_file_name:
            _bf_name = backup_file_name

        return self.copy(self._file_path, os.path.join(os.path.dirname(self._file_path), _bf_name))
