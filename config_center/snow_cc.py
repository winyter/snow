from urllib.parse import quote_plus
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlmodel import create_engine, Session
from contextlib import asynccontextmanager
import fastapi_cdn_host
from pathlib import Path

import ini
from models import (
    CcConfigs,
    CcTemplates,
    CcNamespaces,
    CcRegistryInfo,
    CcConfigsBase,
)
from crud import (
    CrudCcConfigs,
    CrudCcNamespaces,
    CrudCcTemplates,
    create_db_and_tables
)
from errors import (
    CcDataNotFoundError,
    CcTemplateNotFoundError
)
import middlewave


engine = create_engine(
    f"mysql+pymysql://{ini.db_user}:{quote_plus(ini.db_pass)}@{ini.db_host}:{ini.db_port}/{ini.db_name}",
    echo=True if ini.log_level.lower() == 'debug' else False,
    # 后续如果需要支持连接池，可以把该参数改为True
    echo_pool=False,
    connect_args=ini.connect_args
)


def get_session():
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables(engine)
    with Session(engine) as session:
        middlewave.init_snow_configs(session)
    yield
    print('Application Shutdown.')


cc = FastAPI(
    title='Config Center',
    lifespan=lifespan
)
fastapi_cdn_host.patch_docs(cc, Path(__file__).parent / "static")


@cc.get("/", status_code=201, response_model=str)
def hello():
    return PlainTextResponse("Welcome Snow ConfigCenter", status_code=201)


@cc.get("/namespaces", status_code=201, response_model=list[CcNamespaces])
def get_all_namespaces(*, session: Session = Depends(get_session)):
    try:
        return CrudCcNamespaces.read_by_primary(session)
    except CcDataNotFoundError:
        return []


@cc.get("/{namespace}/configs", status_code=201, response_model=list[CcConfigs])
def get_namespace_configs(
        *,
        session: Session = Depends(get_session),
        namespace: str,
):
    try:
        return CrudCcConfigs.read_by_primary(session, namespace=namespace)
    except CcDataNotFoundError:
        raise HTTPException(status_code=404, detail=f"Configs not found (namespace: {namespace})")


@cc.get("/{namespace}/configs/{config_key}", status_code=201, response_model=CcConfigs | str)
def get_config(
        *,
        session: Session = Depends(get_session),
        namespace: str,
        config_key: str,
        only_value: bool = True
):
    try:
        _config = CrudCcConfigs.read_by_primary(session, namespace=namespace, key=config_key)[0]
    except (IndexError, CcDataNotFoundError):
        raise HTTPException(
            status_code=404,
            detail=f"Config not found (namespace: {namespace}, config_key: {config_key}')"
        )
    if only_value:
        return PlainTextResponse(_config.value, status_code=201)
    else:
        return _config


@cc.put("/{namespace}/configs/{config_key}", status_code=201, response_model=CcConfigs)
def update_config_value(
        *,
        session: Session = Depends(get_session),
        namespace: str,
        config_key: str,
        update_row: CcConfigsBase,
):
    if update_row.namespace != namespace or update_row.template_name != config_key:
        raise HTTPException(
            status_code=400,
            detail=f"Input Args mismatch(namespace: {namespace}, config_key: {config_key}, row: {update_row})"
        )
    try:
        return CrudCcConfigs.update_config_value(session, update_row)
    except CcDataNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Config not found ({update_row})"
        )


@cc.get("/{namespace}/templates", status_code=201, response_model=list[CcTemplates])
def get_templates(
        *,
        session: Session = Depends(get_session),
        namespace: str,
):
    return CrudCcTemplates.read_by_primary(session, namespace=namespace)


@cc.get("/{namespace}/templates/{template_name}", status_code=201, response_model=list[CcTemplates])
def get_template_meta(
        *,
        session: Session = Depends(get_session),
        namespace: str,
        template_name: str
):
    try:
        return CrudCcTemplates.read_by_primary(session, namespace=namespace, template_name=template_name)
    except CcDataNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found (namespace: {namespace}, template_name: {template_name})"
        )


@cc.put("/{namespace}/templates/{template_name}", status_code=201, response_model=CcTemplates)
def update_template_info(
        *,
        session: Session = Depends(get_session),
        namespace: str,
        template_name: str,
        update_row: CcTemplates
):
    if update_row.namespace != namespace or update_row.template_name != template_name:
        raise HTTPException(
            status_code=400,
            detail=f"Input Args mismatch(namespace: {namespace}, template_name: {template_name}, row: {update_row})"
        )
    try:
        return CrudCcTemplates.update_dest_info(
            session,
            new_row=update_row
        )
    except CcDataNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found (namespace: {namespace}, template_name: {template_name})"
        )


@cc.get("/{namespace}/templates/{template_name}/render", status_code=201, response_model=None)
def render_template(
        *,
        session: Session = Depends(get_session),
        namespace: str,
        template_name: str,
):
    try:
        middlewave.deploy_template(session, namespace, template_name)
    except CcDataNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Template or Namespace not found (namespace: {namespace}, template_name: {template_name})")
    except CcTemplateNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Template file not found (namespace: {namespace}, template_name: {template_name})")


@cc.post("/registry/wizard", status_code=201, response_model=str)
def registry_wizard(
        *,
        session: Session = Depends(get_session),
        namespace: str
):
    if namespace == ini.snow_namespace:
        raise HTTPException(
            status_code=400,
            detail=f"The namespace is snow's namespace, Change it.")
    try:
        return PlainTextResponse(
            middlewave.execute_wizard(
                db_session=session,
                namespace=namespace
            ),
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{e}")


@cc.post("/registry/register", status_code=201)
def registry_register(
        *,
        session: Session = Depends(get_session),
        data: CcRegistryInfo
):
    if data.namespace == ini.snow_namespace:
        raise HTTPException(
            status_code=400,
            detail=f"The namespace is snow's namespace, Change it.")
    middlewave.registry(
        db_session=session,
        data=data
    )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        f"{Path(__file__).stem}:cc",
        host='0.0.0.0',
        port=int(ini.api_port),
        reload=False,
        workers=1
    )
