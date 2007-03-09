from zope.component import getUtility
from zope.component import queryUtility

from Products.CMFPlone.interfaces import IFactoryTool
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import exportObjects

try:
    set()
except NameError:
    from sets import Set as set


class PortalFactoryXMLAdapter(XMLAdapterBase):
    """In- and exporter for FactoryTool.
    """

    __used_for__ = IFactoryTool

    _LOGGER_ID = name = 'factorytool'

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode("object")
        node.appendChild(self._extractFactoryToolSettings())

        self._logger.info("FactoryTool settings exported.")
        return node

    def _importNode(self, node):
        if self.environ.shouldPurge():
            self._purgeFactoryToolSettings()

        self._initFactoryToolSettings(node)
        self._logger.info("FactoryTool settings imported.")

    def _purgeFactoryToolSettings(self):
        self.context.manage_setPortalFactoryTypes(listOfTypeIds=[])


    def _initFactoryToolSettings(self, node):
        for child in node.childNodes:
            if child.nodeName=="factorytypes":
                types=set(self.context.getFactoryTypes())
                for type in child.getElementsByTagName("type"):
                    types.add(type.getAttribute("portal_type"))
                self.context.manage_setPortalFactoryTypes(
                                    listOfTypeIds=list(types))


    def _extractFactoryToolSettings(self):
        node=self._doc.createElement("factorytypes")
        for type in self.context.getFactoryTypes():
            child=self._doc.createElement("type")
            child.setAttribute("portal_type", type)
            node.appendChild(child)

        return node


def importFactoryTool(context):
    """Import Factory Tool configuration.
    """
    site = context.getSite()
    tool = getUtility(IFactoryTool)

    importObjects(tool, '', context)


def exportFactoryTool(context):
    """Export Factory Tool configuration.
    """
    site = context.getSite()
    tool = queryUtility(IFactoryTool)
    if tool is None:
        logger = context.getLogger("factorytool")
        logger.info("Nothing to export.")
        return

    exportObjects(tool, '', context)
