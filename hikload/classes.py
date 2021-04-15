class ResponseObject(object):
    def __init__(self, camera: str, name: str, starttime: str, endtime: str):
        self.camera = camera
        self.name = name
        self.starttime = starttime
        self.endtime = endtime
        self.url = ""
    pass


class InvalidResponseException(Exception):
    """Raised when the response is not valid"""
    pass
