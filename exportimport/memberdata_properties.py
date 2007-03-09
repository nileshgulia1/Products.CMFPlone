"""MemberData tool properties setup handlers.

$Id:$
"""

from zope.app import zapi
from zope.component import getUtility
from zope.component import queryUtility
from Products.CMFCore.interfaces import IMemberDataTool
from Products.GenericSetup.interfaces import IBody

_FILENAME = 'memberdata_properties.xml'

def importMemberDataProperties(context):
    """ Import MemberData tool properties.
    """
    site = context.getSite()
    logger = context.getLogger('memberdata')
    ptool = getUtility(IMemberDataTool)

    body = context.readDataFile(_FILENAME)
    if body is None:
        logger.info('Nothing to import.')
        return

    importer = zapi.queryMultiAdapter((ptool, context), IBody)
    if importer is None:
        logger.warning('Import adapter missing.')
        return

    importer.body = body
    logger.info('MemberData tool imported.')

def exportMemberDataProperties(context):
    """ Export MemberData tool properties .
    """
    site = context.getSite()
    logger = context.getLogger('memberdata')
    ptool = queryUtility(IMemberDataTool)
    if ptool is None:
        logger.info('Nothing to export.')
        return

    exporter = zapi.queryMultiAdapter((ptool, context), IBody)
    if exporter is None:
        logger.warning('Export adapter missing.')
        return

    context.writeDataFile(_FILENAME, exporter.body, exporter.mime_type)
    logger.info('MemberData tool exported.')
