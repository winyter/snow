import os
from typing import List

import ini


# 模板库操作类
class TemplatesLibHandle:
    @classmethod
    def search_templates(cls, namespace: str, config_keys: List[str]) -> List[str]:
        library_path = os.path.join(ini.resources_path, namespace)

        _result_templates = []
        for _t in os.listdir(library_path):
            if os.path.isfile(os.path.join(library_path, _t)):
                with open(os.path.join(library_path, _t), encoding='utf-8', mode='r') as f:
                    content = f.read()
                for _c in config_keys:
                    if '{{ '+_c+' }}' in content:
                        _result_templates.append(_t)
                        break
        return _result_templates
