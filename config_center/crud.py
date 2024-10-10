import datetime
from typing import List, NoReturn, Optional, Iterable
from sqlmodel import SQLModel, Session, select
from jinja2.exceptions import TemplateSyntaxError

from models import CcConfigs, CcNamespaces, CcTemplates, CcConfigsBase
from errors import (
    CcDataNotFoundError,
    CcRenderError,
    CcDataDeleteError
)
from utils.jinja_handler import JinjaHandler


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)


class Crud:
    @classmethod
    def create(cls, db: Session, rows: List) -> NoReturn:
        for row in rows:
            db.add(row)
        db.commit()

    @classmethod
    def delete(cls, db: Session, statement) -> NoReturn:
        all_row = db.exec(statement).all()

        for _r in all_row:
            db.delete(_r)
        db.commit()

        if db.exec(statement).all():
            raise CcDataDeleteError(f'Table delete rows failed.')

    @classmethod
    def _render_value(cls, raw_value: str, **envs) -> str:
        try:
            _rendered_value = JinjaHandler.render(raw_value, **envs)
        except TypeError:
            # 处理报错：TypeError: Can't compile non template nodes（当被渲染的内容为None时会触发此报错），当渲染内容值为None，就认为这个字段本身就没有值，即对其赋值空字符串
            _rendered_value = ''
        except TemplateSyntaxError:
            raise CcRenderError(f"Syntax Error: Raw content: {raw_value}")
        return _rendered_value


class CrudCcConfigs(Crud):
    @classmethod
    def create(cls, db: Session, rows: Iterable[CcConfigs], **render_envs) -> NoReturn:
        rows = list(map(
            lambda _: CcConfigs(
                namespace=_.namespace,
                key=_.key,
                value=cls._render_value(_.value, **render_envs),
                description=_.description,
                category=_.category
            ),
            rows
        ))
        super().create(db, rows)

    @classmethod
    def update_config_value(
            cls,
            db: Session,
            data: CcConfigsBase,
            **render_envs
    ) -> CcConfigs:
        row = db.exec(select(CcConfigs).where(CcConfigs.namespace == data.namespace).where(CcConfigs.key == data.key)).first()
        if row:
            row.value = cls._render_value(data.value, **render_envs)
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
        else:
            raise CcDataNotFoundError

    @classmethod
    def read_by_primary(
            cls,
            db: Session,
            namespace: Optional[str] = None,
            key: Optional[str] = None
    ) -> List[CcConfigs]:
        statement = select(CcConfigs)
        if namespace is not None:
            statement = statement.where(CcConfigs.namespace == namespace)
        if key is not None:
            statement = statement.where(CcConfigs.key == key)

        result = db.exec(statement).all()
        if result:
            return result
        else:
            raise CcDataNotFoundError

    @classmethod
    def delete_all_namespace_rows(cls, db: Session, namespace: str) -> NoReturn:
        super().delete(db, select(CcConfigs).where(CcConfigs.namespace == namespace))


class CrudCcNamespaces(Crud):
    @classmethod
    def create(cls, db: Session, row: CcNamespaces) -> NoReturn:
        super().create(db, [row])

    @classmethod
    def update(
            cls,
            db: Session,
            namespace: str,
            version: Optional[str] = None
    ) -> CcNamespaces:
        row = db.exec(select(CcNamespaces).where(CcNamespaces.namespace == namespace)).first()
        if row:
            is_change = 0
            if version and row.version != version:
                row.version = version
                is_change += 1
            if is_change:
                row.update_time = datetime.datetime.now()
                db.add(row)
                db.commit()
                db.refresh(row)
            return row
        else:
            raise CcDataNotFoundError

    @classmethod
    def read_by_primary(
            cls,
            db: Session,
            namespace: Optional[str] = None,
    ) -> List[CcNamespaces]:
        statement = select(CcNamespaces)
        if namespace:
            statement = statement.where(CcNamespaces.namespace == namespace)

        result = db.exec(statement).all()
        if result:
            return result
        else:
            raise CcDataNotFoundError


class CrudCcTemplates(Crud):
    @classmethod
    def create(cls, db: Session, rows: List[CcTemplates], **render_envs):
        rows = list(map(
            lambda x: CcTemplates(
                namespace=x.namespace,
                template_name=x.template_name,
                dest_address=cls._render_value(x.dest_address, **render_envs),
                dest_path=cls._render_value(x.dest_path, **render_envs),
                dest_user=cls._render_value(x.dest_user, **render_envs),
                dest_passwd=cls._render_value(x.dest_passwd, **render_envs)
            ),
            rows
        ))
        super().create(db, rows)

    @classmethod
    def delete_all_namespace_rows(cls, db: Session, namespace: str) -> NoReturn:
        super().delete(db, select(CcTemplates).where(CcTemplates.namespace == namespace))

    @classmethod
    def read_by_primary(
            cls,
            db: Session,
            namespace: Optional[str] = None,
            template_name: Optional[str] = None
    ) -> List[CcTemplates]:
        statement = select(CcTemplates)
        if namespace is not None:
            statement = statement.where(CcTemplates.namespace == namespace)
        if template_name is not None:
            statement = statement.where(CcTemplates.template_name == template_name)

        return db.exec(statement).all()

    @classmethod
    def update_dest_info(
            cls,
            db: Session,
            new_row: CcTemplates,
            **render_envs
    ) -> CcTemplates:
        row = db.exec(
            select(
                CcTemplates
            ).where(
                CcTemplates.namespace == new_row.namespace
            ).where(
                CcTemplates.template_name == new_row.template_name
            )
        ).first()

        if row:
            row.dest_address = cls._render_value(new_row.dest_address, **render_envs),
            row.dest_path = cls._render_value(new_row.dest_path, **render_envs),
            row.dest_user = cls._render_value(new_row.dest_user, **render_envs),
            row.dest_passwd = cls._render_value(new_row.dest_passwd, **render_envs)
            db.add(row)
            db.commit()
            db.refresh(row)
            return row
        else:
            raise CcDataNotFoundError
