import logging
import requests
from requests.auth import HTTPDigestAuth
from lxml import etree
from collections import OrderedDict
from io import BytesIO
from xmler import dict2xml as d2xml


class HikvisionServer:
    """This is a class for storing basic info about a DVR.

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


def getXML(server: HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    logging.debug("Data sent: %s" % tosend)
    response = xml2dict(getXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise Exception(response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise Exception(response['userCheck']['statusString'])
    return response


def getXMLRaw(server: HikvisionServer, path: str, xmldata: str = None) -> dict:
    """
    This returns the response of the DVR to the following GET request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    headers = {'Content-Type': 'application/xml'}
    if xmldata is None:
        responseRaw = requests.get(
            server.address() + path,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.get(
            server.address() + path,
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    responseXML = responseRaw.text
    return responseXML


def putXML(server: HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    logging.debug("Data sent: %s" % tosend)
    response = xml2dict(putXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise Exception(response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise Exception(response['userCheck']['statusString'])
    return response


def putXMLRaw(server: HikvisionServer, path: str, xmldata: str = None) -> dict:
    """
    This returns the response of the DVR to the following PUT request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    headers = {'Content-Type': 'application/xml'}
    if xmldata is None:
        responseRaw = requests.put(
            server.address() + path,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.put(
            server.address() + path,
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    responseXML = responseRaw.text
    return responseXML


def deleteXMLRaw(server: HikvisionServer, path, xmldata=None) -> dict:
    """
    This returns the response of the DVR to the following DELETE request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    headers = {'Content-Type': 'application/xml'}
    if xmldata is None:
        responseRaw = requests.delete(
            server.address() + path,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.delete(
            server.address() + path,
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    if responseRaw.status_code == 401:
        raise Exception("Wrong username or password")
    responseXML = responseRaw.text
    return responseXML


def postXML(server: HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    logging.debug("Data sent: %s" % tosend)
    response = xml2dict(postXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise Exception(response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise Exception(response['userCheck']['statusString'])
    return response


def postXMLRaw(server: HikvisionServer, path: str, xmldata: str = None) -> dict:
    """
    This returns the response of the DVR to the following POST request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    headers = {'Content-Type': 'application/xml'}
    responseRaw = requests.post(
        server.address() + path,
        data=xmldata,
        headers=headers,
        auth=HTTPDigestAuth(server.user, server.password))
    responseXML = responseRaw.text
    return responseXML


def xml2dict(xml: str) -> dict:
    """Converts string formatted for the DVR to a dict

    Parameters:
        xml (string): The XML string

    Returns:
        dictionary (dict): The resulting dictionary
                           This has `@attrs` in place of the attributes
    """
    # Taken from https://stackoverflow.com/questions/4255277/
    xslt = b"""<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="no"/>

    <xsl:template match="/|comment()|processing-instruction()">
        <xsl:copy>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="*">
        <xsl:element name="{local-name()}">
            <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>
</xsl:stylesheet>
"""
    if type(xml) == str:
        xml = bytes(xml, "UTF8")

    xmlstr = BytesIO(xml)
    parser = etree.XMLParser(ns_clean=True)
    tree = etree.parse(xmlstr, parser=parser)

    xslt_doc = etree.parse(BytesIO(xslt))
    transform = etree.XSLT(xslt_doc)
    tree = transform(tree)

    return tree2dict(tree.getroot())


def tree2dict(node):
    subdict = OrderedDict({})
    # iterate over the children of this element--tree.getroot
    for e in node.iterchildren():
        d = tree2dict(e)
        for k in d.keys():
            # handle duplicated tags
            if k in subdict:
                v = subdict[k]
        # use append to assert exception
                try:
                    v.append(d[k])
                    subdict.update({k: v})
                except AttributeError:
                    subdict.update({k: [v, d[k]]})
            else:
                subdict.update(d)
    if subdict:
        attribdict = dict()
        for i in node.attrib:
            val = node.attrib[i]
            attribdict[str(i)] = val
        subdict.update({"@attrs": attribdict})
        return {node.tag: subdict}
    else:
        return {node.tag: node.text}


def dict2xml(dictionary: dict) -> str:
    """Converts a dict to a string formatted for the DVR

    Parameters:
        dictionary (dict): The resulting dictionary
                           This has `@attrs` in place of the attributes

    Returns:
        xml (string): The XML string
    """
    for i in dictionary:
        dictionary[i]["@attrs"].update(
            {"xmlns": "http://www.hikvision.com/ver20/XMLSchema"})
    xml = d2xml(dictionary)
    return """<?xml version = "1.0" encoding = "UTF-8" ?>""" + str(xml)
