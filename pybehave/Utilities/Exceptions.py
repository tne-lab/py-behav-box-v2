class InvalidComponentTypeError(BaseException):
    pass


class ComponentRegisterError(BaseException):
    pass


class MalformedProtocolError(BaseException):
    pass


class MalformedAddressFileError(BaseException):
    pass


class SourceUnavailableError(BaseException):
    pass


class AddTaskError(BaseException):
    pass


class MissingExtraError(BaseException):
    def __init__(self, extra: str):
        self.extra = extra
