import re
from typing import NoReturn
import paramiko


class CommandExecError(Exception):
    pass


class HighRiskCommandError(Exception):
    pass


high_risk_commands_res = (
    r'^rm -[a-z|A-Z]*r[a-z|A-Z]* \*',
    r'^rm -[a-z|A-Z]*r[a-z|A-Z]* /*/\*',
    r'^rm -[a-z|A-Z]*r[a-z|A-Z]* /\*'
)


def null_debug_log_handle(log_content: str):
    pass


class SSHConnectHandle:
    def __init__(
            self,
            host: str,
            port: str | int,
            username: str,
            password: str,
            debug_log_handle=null_debug_log_handle
    ):
        self._debug_log_handle = debug_log_handle
        self._ssh_handle = paramiko.SSHClient()
        self._ssh_handle.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh_handle.connect(host, port=port, username=username, password=password)
        self._debug_log_handle(f'连接已建立：{self._ssh_handle}')

    def exec_command(
            self,
            command: str,
            is_return_stdout: bool = False
    ) -> str:
        """
        :param command: Linux command
        :param is_return_stdout: 是否返回 stdout，默认不返回
        :return: stdout
        """
        for _r in high_risk_commands_res:
            if re.search(_r, command):
                raise HighRiskCommandError(f'High Risk Command, forbidden exec: {command}')

        self._debug_log_handle(f'执行命令：{command}')
        stdin, stdout, stderr = self._ssh_handle.exec_command(command, get_pty=True)
        stderr_list = stderr.readlines()
        stdout_str = stdout.read().decode('utf-8')
        self._debug_log_handle(f'\nstdout: \n{stdout_str}')
        self._debug_log_handle(f'\nstderr: \n{stderr_list}')

        if stdout.channel.recv_exit_status() != 0:
            raise CommandExecError(f'\nstdout: {stdout_str}\nstderr: {stderr_list}')
        else:
            if is_return_stdout:
                return stdout_str

    def close_connect(self) -> NoReturn:
        self._debug_log_handle(f'关闭连接：{self._ssh_handle}')
        self._ssh_handle.close()
