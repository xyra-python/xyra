class XyraException(Exception):
    pass

class HTTPException(XyraException):
    def __init__(self, status_code: int, detail: str = None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")

class WebSocketException(XyraException):
    def __init__(self, code: int, reason: str = None):
        self.code = code
        self.reason = reason
        super().__init__(f"{code}: {reason}")