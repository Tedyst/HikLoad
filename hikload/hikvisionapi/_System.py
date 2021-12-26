import hikload.hikvisionapi as hikvisionapi


class _System():
    def __init__(self, parent):
        self.parent = parent

    def getDeviceInfo(self):
        """
        Returns the device info as a dictionary
        """
        return hikvisionapi.getXML(self.parent, "System/deviceInfo")

    def activateDevice(self, password: str):
        """
        It is used to activate device
        """
        xml = hikvisionapi.xml2dict(b'\
        <ActivateInfo version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">\
        <password></password>\
        </ActivateInfo>')
        xml['ActivateInfo']['password'] = password
        data = hikvisionapi.dict2xml(xml)

        return hikvisionapi.postXML(self.parent, "System/activate", data)

    def getCapabilities(self):
        """
        It is used to get device capability.
        """
        return hikvisionapi.getXML(self.parent, "System/capabilities")

    def reboot(self):
        """
        Reboot the device.
        """
        return hikvisionapi.putXML(self.parent, "System/reboot")

    def getConfigurationData(self):
        """
        Get device’s configuration data.
        """
        return hikvisionapi.getXML(self.parent, "System/configurationData")

    def factoryReset(self):
        """
        Get device’s configuration data.
        """
        return hikvisionapi.putXML(self.parent, "System/factoryReset")
