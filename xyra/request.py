from socketify import HttpRequest

class Request:
    def __init__(self, req: HttpRequest, params=None):
        req.preserve()
        self._req = req
        self.params = params or {}

    @property
    def method(self):
        return self._req.get_method()

    @property
    def url(self):
        return self._req.get_url()

    @property
    def headers(self):
        headers = {}
        self._req.for_each_header(lambda key, value: headers.update({key: value}))
        return headers

    @property
    def query(self):
        return self._req.get_query()

    def get_parameter(self, index: int):
        return self._req.get_parameter(index)