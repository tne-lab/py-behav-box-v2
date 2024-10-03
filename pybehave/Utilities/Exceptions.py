class ChamberException(BaseException):
    def __init__(self, chamber: int):
        self.chamber = chamber


class InvalidComponentTypeError(ChamberException):
    pass


class ComponentRegisterError(ChamberException):
    pass


class MalformedProtocolError(ChamberException):
    pass


class MalformedAddressFileError(ChamberException):
    pass


class SourceUnavailableError(ChamberException):
    def __init__(self, chamber: int, sid: str):
        super().__init__(chamber)
        self.sid = sid


class ComponentUnavailableError(ChamberException):
    def __init__(self, chamber: int, cid: str):
        super().__init__(chamber)
        self.cid = cid


class AddTaskError(ChamberException):
    pass


class MissingExtraError(BaseException):
    def __init__(self, extra: str):
        self.extra = extra
