from hikload.hikvisionapi._System import _System
from hikload.hikvisionapi._Streaming import _Streaming
from hikload.hikvisionapi._ContentMgmt import _ContentMgmt
from requests.exceptions import ConnectionError


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
        self.ContentMgmt = _ContentMgmt(self)

    def __repr__(self) -> str:
        return "%s(host=%s, protocol=%s, user=%s)" % (self.__class__.__name__, self.host, self.protocol, self.user)

    def __eq__(self, o: object) -> bool:
        if o.__class__ is self.__class__:
            return (self.host, self.protocol, self.user, self.password) == (o.host, o.protocol, o.user, o.password)
        else:
            return NotImplemented

    def __ne__(self, o: object) -> bool:
        result = self.__eq__(o)
        if result is NotImplemented:
            return NotImplemented
        else:
            return not result

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

    def test_connection(self):
        """This method tests the connection to the DVR"""
        try:
            self.System.getDeviceInfo()
        except HikvisionException as e:
            raise HikvisionException("Error while testing connection: %s" % e)
        except ConnectionError as e:
            raise HikvisionException("Error while testing connection: %s" % e)


class Hasher(dict):
    # https://stackoverflow.com/a/3405143/190597
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
