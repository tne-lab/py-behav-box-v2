class ChamberException(BaseException):
    chamber: int


class InvalidComponentTypeError(ChamberException):
    pass


class ComponentRegisterError(ChamberException):
    pass


class MalformedProtocolError(ChamberException):
    pass


class MalformedAddressFileError(ChamberException):
    pass


class SourceUnavailableError(ChamberException):
    sid: str


class ComponentUnavailableError(ChamberException):
    cid: str


class AddTaskError(ChamberException):
    pass


class MissingExtraError(BaseException):
    extra: str
