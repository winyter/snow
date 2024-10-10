class CcError(Exception):
    pass


class CcIniError(CcError):
    pass


class CcDataError(CcError):
    pass


class CcDataNotFoundError(CcDataError):
    pass


class CcDataDeleteError(CcDataError):
    pass


class CcResourcesError(CcError):
    pass


class CcTemplateNotFoundError(CcResourcesError):
    pass


class CcMetaIllegalError(CcResourcesError):
    pass


class CcRenderError(CcError):
    pass
