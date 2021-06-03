from hikvisionapi._System import _System
from hikvisionapi._Streaming import _Streaming


class HikvisionException(Exception):
    pass


class HikvisionServer:
    """This is a class for storing basic info about a DVR/NVR.

    Parameters:
        host (str): The host address, without `http` or `https`
        user (str): The username for the DVR
        password (str): The password
        protocol (str): The intended protocol
                        Should be `http`(default) or `https`
    """

    def __init__(self, host, user, password, protocol="http"):
        self.host = host
        self.protocol = protocol
        self.user = user
        self.password = password
        self.System = _System(self)
        self.Streaming = _Streaming(self)

    def address(self, protocol: bool = True, credentials: bool = True):
        """This returns the formatted address of the DVR

        Parameters:
            protocol (bool): Includes the `http`/`https` part in URL (default is True)
            credentials (bool): Includes the credentials in URL (default is True)
        """
        string = ""
        if protocol:
            string += self.protocol + "://"
        if credentials:
            string += "%s:%s@" % (self.user, self.password)
        string += self.host + "/ISAPI"
        return string
