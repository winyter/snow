from datetime import datetime
from sqlmodel import Field, SQLModel


class CcBase(SQLModel):
    namespace: str = Field(primary_key=True)


class CcNamespaces(CcBase, table=True):
    __tablename__ = 'cc_namespaces'

    version: str
    update_time: datetime = datetime.now()


class CcConfigsBase(CcBase):
    key: str = Field(primary_key=True)
    value: str | None


class CcConfigs(CcConfigsBase, table=True):
    __tablename__ = 'cc_configs'

    description: str
    category: str


class CcTemplates(CcBase, table=True):
    __tablename__ = 'cc_templates'

    template_name: str = Field(primary_key=True)
    dest_address: str
    dest_path: str
    dest_user: str
    dest_passwd: str


class CcRegistryInfo(CcBase):
    wizard_configs: str
