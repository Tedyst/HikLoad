import hikload.hikvisionapi as hikvisionapi
import logging
from collections import OrderedDict
from io import BytesIO
from typing import Union
import copy
import os

import requests
from lxml import etree
from requests.auth import HTTPDigestAuth
from xmler import dict2xml as d2xml

logger = logging.getLogger('hikload')


def getXML(server: hikvisionapi.HikvisionServer, path: str, data: dict = None, xmldata: str = None, rawResponse: bool = False) -> dict:
    """This returns the response of the DVR to the following GET request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        data (dict): This is the data that will be transmitted to the server.
                     It is optional, and will overwrite `xmldata`
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    if tosend is not None:
        logger.debug("Data sent: %s" % tosend)
    if rawResponse:
        return getXMLRaw(server, path, xmldata=tosend, rawResponse=True)
    response = xml2dict(getXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise hikvisionapi.HikvisionException(
                    response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise hikvisionapi.HikvisionException(
                response['userCheck']['statusString'])
    return response


def getXMLRaw(server: hikvisionapi.HikvisionServer, path: str, xmldata: str = None, rawResponse: bool = False) -> dict:
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
        logger.debug("%s/%s" % (server.address(), path))
        responseRaw = requests.get(
            "%s/%s" % (server.address(), path),
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.get(
            "%s/%s" % (server.address(), path),
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    if rawResponse:
        return responseRaw
    responseXML = responseRaw.text
    return responseXML


def putXML(server: hikvisionapi.HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    """This returns the response of the DVR to the following PUT request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        data (dict): This is the data that will be transmitted to the server.
                     It is optional, and will overwrite `xmldata`
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    if tosend is not None:
        logger.debug("Data sent: %s" % tosend)
    response = xml2dict(putXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise hikvisionapi.HikvisionException(
                    response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise hikvisionapi.HikvisionException(
                response['userCheck']['statusString'])
    return response


def putXMLRaw(server: hikvisionapi.HikvisionServer, path: str, xmldata: str = None) -> dict:
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
            "%s/%s" % (server.address(), path),
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.put(
            "%s/%s" % (server.address(), path),
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    responseXML = responseRaw.text
    return responseXML


def deleteXML(server: hikvisionapi.HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    """This returns the response of the DVR to the following DELETE request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        data (dict): This is the data that will be transmitted to the server.
                     It is optional, and will overwrite `xmldata`
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    if tosend is not None:
        logger.debug("Data sent: %s" % tosend)
    response = xml2dict(deleteXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise hikvisionapi.HikvisionException(
                    response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise hikvisionapi.HikvisionException(
                response['userCheck']['statusString'])
    return response


def deleteXMLRaw(server: hikvisionapi.HikvisionServer, path: str, xmldata=None) -> dict:
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
            "%s/%s" % (server.address(), path),
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    else:
        responseRaw = requests.delete(
            "%s/%s" % (server.address(), path),
            data=xmldata,
            headers=headers,
            auth=HTTPDigestAuth(server.user, server.password))
    if responseRaw.status_code == 401:
        raise hikvisionapi.HikvisionException("Wrong username or password")
    responseXML = responseRaw.text
    return responseXML


def postXML(server: hikvisionapi.HikvisionServer, path: str, data: dict = None, xmldata: str = None) -> dict:
    """This returns the response of the DVR to the following POST request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        data (dict): This is the data that will be transmitted to the server.
                     It is optional, and will overwrite `xmldata`
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    tosend = xmldata
    if data:
        tosend = dict2xml(data)
    if tosend is not None:
        logger.debug("Data sent: %s" % tosend)
    response = xml2dict(postXMLRaw(server, path, xmldata=tosend))
    if 'ResponseStatus' in response:
        if 'statusCode' in response['ResponseStatus']:
            if response['ResponseStatus']['statusCode'] != '1':
                raise hikvisionapi.HikvisionException(
                    response['ResponseStatus']['statusString'])
    if 'userCheck' in response:
        if response['userCheck']['statusValue'] != 200:
            raise hikvisionapi.HikvisionException(
                response['userCheck']['statusString'])
    return response


def postXMLRaw(server: hikvisionapi.HikvisionServer, path: str, xmldata: str = None) -> dict:
    """This returns the response of the DVR to the following POST request

    Parameters:
        server (HikvisionServer): The basic info about the DVR
        path (str): The ISAPI path that will be executed
        xmldata (str): This should be formatted using `utils.dict2xml`
                       This is the data that will be transmitted to the server.
                       It is optional.
    """
    headers = {'Content-Type': 'application/xml'}
    responseRaw = requests.post(
        "%s/%s" % (server.address(), path),
        data=xmldata,
        headers=headers,
        auth=HTTPDigestAuth(server.user, server.password))
    responseXML = responseRaw.text
    return responseXML


def xml2dict(xml: Union[str, dict]) -> dict:
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

    return hikvisionapi.classes.Hasher(tree2dict(tree.getroot()))


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
    # Keep the original dictionary intact, in case it needs to be modified
    temp = copy.deepcopy(dictionary)
    for i in temp:
        temp[i]["@attrs"].update(
            {"xmlns": "http://www.hikvision.com/ver20/XMLSchema"})
    xml = d2xml(temp)
    return """<?xml version = "1.0" encoding = "UTF-8" ?>""" + str(xml)
