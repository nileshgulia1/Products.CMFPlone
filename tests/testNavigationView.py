#
# Test methods used to make ...
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.publisher.browser import setDefaultSkin
from zope.interface import directlyProvides

from Products.CMFPlone.tests import PloneTestCase
from Products.CMFPlone.tests import dummy

from Products.CMFPlone.browser.navigation import CatalogNavigationTree
from Products.CMFPlone.browser.navigation import CatalogSiteMap
from Products.CMFPlone.browser.navigation import CatalogNavigationTabs
from Products.CMFPlone.browser.navigation import CatalogNavigationBreadcrumbs
from Products.CMFPlone.browser.navigation import PhysicalNavigationBreadcrumbs
from Products.CMFPlone.interfaces import IHideFromBreadcrumbs

portal_name = PloneTestCase.portal_name


class TestBaseNavTree(PloneTestCase.PloneTestCase):
    """Tests for the navigation tree . This base test is a little geared toward 
       a catalog based implementation for now.
    """

    view_class = None

    def afterSetUp(self):
        self.request = self.app.REQUEST
        # Apply a default layer for view lookups to work in Zope 2.9+
        setDefaultSkin(self.request)
        self.populateSite()
        
    def populateSite(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'doc1')
        self.portal.invokeFactory('Document', 'doc2')
        self.portal.invokeFactory('Document', 'doc3')
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Link', 'link1')
        self.portal.link1.setRemoteUrl('http://plone.org')
        self.portal.link1.reindexObject()
        folder1 = getattr(self.portal, 'folder1')
        folder1.invokeFactory('Document', 'doc11')
        folder1.invokeFactory('Document', 'doc12')
        folder1.invokeFactory('Document', 'doc13')
        self.portal.invokeFactory('Folder', 'folder2')
        folder2 = getattr(self.portal, 'folder2')
        folder2.invokeFactory('Document', 'doc21')
        folder2.invokeFactory('Document', 'doc22')
        folder2.invokeFactory('Document', 'doc23')
        folder2.invokeFactory('File', 'file21')
        self.setRoles(['Member'])

    def testCreateNavTree(self):
        # See if we can create one at all
        view = self.view_class(self.portal, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))

    def testCreateNavTreeCurrentItem(self):
        # With the context set to folder2 it should return a dict with
        # currentItem set to True
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['currentItem'], True)

    def testNavTreeExcludesItemsWithExcludeProperty(self):
        # Make sure that items witht he exclude_from_nav property set get
        # no_display set to True
        self.portal.folder2.setExcludeFromNav(True)
        self.portal.folder2.reindexObject()
        view = self.view_class(self.portal.folder1.doc11, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        for c in tree['children']:
            if c['item'].getPath() == '/plone/folder2':
                self.fail()

    def testShowAllParentsOverridesNavTreeExcludesItemsWithExcludeProperty(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        self.portal.folder2.setExcludeFromNav(True)
        self.portal.folder2.reindexObject()
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(showAllParents=True)
        view = self.view_class(self.portal.folder2.doc21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        found = False
        for c in tree['children']:
            if c['item'].getPath() == '/plone/folder2':
                found = True
                break
        self.failUnless(found)

    def testNavTreeExcludesItemsInIdsNotToList(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(idsNotToList=['folder2'])
        view = self.view_class(self.portal.folder1.doc11, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        for c in tree['children']:
            if c['item'].getPath() == '/plone/folder2':
                self.fail()

    def testShowAllParentsOverridesNavTreeExcludesItemsInIdsNotToList(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property are not included
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(idsNotToList=['folder2'], showAllParents=True)
        view = self.view_class(self.portal.folder2.doc21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        found = False
        for c in tree['children']:
            if c['item'].getPath() == '/plone/folder2':
                found = True
                break
        self.failUnless(found)

    def testNavTreeExcludesDefaultPage(self):
        # Make sure that items which are the default page are excluded
        self.portal.folder2.setDefaultPage('doc21')
        view = self.view_class(self.portal.folder1.doc11, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        # Ensure that our 'doc21' default page is not in the tree.
        self.assertEqual([c for c in tree['children'][-1]['children']
                                            if c['item'].getPath()[-5:]=='doc21'],[])

    def testNavTreeMarksParentMetaTypesNotToQuery(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property get no_display set to True
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.assertEqual(tree['children'][-1]['show_children'],True)
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(parentMetaTypesNotToQuery=['Folder'])
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.assertEqual(tree['children'][-1]['show_children'],False)

    def testCreateNavTreeWithLink(self):
        view = self.view_class(self.portal, self.request)
        tree = view.navigationTree()
        for child in tree['children']:
            if child['portal_type'] != 'Link':
                self.failIf(child['item'].getRemoteUrl)
            if child['Title'] == 'link1':
                self.failUnlessEqual(child['item'].getRemoteUrl, 'http://plone.org')

    def testNonStructuralFolderHidesChildren(self):
        # Make sure NonStructuralFolders act as if parentMetaTypesNotToQuery
        # is set.
        f = dummy.NonStructuralFolder('ns_folder')
        self.folder._setObject('ns_folder', f)
        self.portal.portal_catalog.reindexObject(self.folder.ns_folder)
        self.portal.portal_catalog.reindexObject(self.folder)
        view = self.view_class(self.folder.ns_folder, self.request)
        tree = view.navigationTree()
        self.assertEqual(tree['children'][0]['children'][0]['children'][0]['item'].getPath(),
                                '/plone/Members/test_user_1_/ns_folder')
        self.assertEqual(len(tree['children'][0]['children'][0]['children'][0]['children']), 0)

    def testTopLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['item'].getPath(), '/plone/folder2/file21')

    def testTopLevelWithContextAboveLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        view = self.view_class(self.portal, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 0)

    def testTopLevelTooDeep(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=5)
        view = self.view_class(self.portal, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 0)

    def testTopLevelWithNavigationRoot(self):
        self.portal.folder2.invokeFactory('Folder', 'folder21')
        self.portal.folder2.folder21.invokeFactory('Document', 'doc211')
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1, root='/folder2')
        view = self.view_class(self.portal.folder2.folder21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(len(tree['children']), 1)
        self.assertEqual(tree['children'][0]['item'].getPath(), '/plone/folder2/folder21/doc211')

    def testTopLevelWithPortalFactory(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        id=self.portal.generateUniqueId('Document')
        typeName='Document'
        newObject=self.portal.folder1.restrictedTraverse('portal_factory/' + typeName + '/' + id)
        # Will raise a KeyError unless bug is fixed
        view = self.view_class(newObject, self.request)
        tree = view.navigationTree()
    
    def testShowAllParentsOverridesBottomLevel(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        # Note: showAllParents makes sure we actually return items on the,
        # path to the context, but the portlet will not display anything
        # below bottomLevel. 
        self.assertEqual(tree['children'][-1]['item'].getPath(), '/plone/folder2')
        self.assertEqual(len(tree['children'][-1]['children']), 1)
        self.assertEqual(tree['children'][-1]['children'][0]['item'].getPath(), '/plone/folder2/file21')
        
    def testBottomLevelStopsAtFolder(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['item'].getPath(), '/plone/folder2')
        self.assertEqual(len(tree['children'][-1]['children']), 0)
        
    def testNoRootSet(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='')
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['item'].getPath(), '/plone/folder2')
        
    def testRootIsPortal(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/')
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][-1]['item'].getPath(), '/plone/folder2')
        
    def testRootIsNotPortal(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/folder2')
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['item'].getPath(), '/plone/folder2/doc21')

    def testRootDoesNotExist(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/dodo')
        view = self.view_class(self.portal.folder2.file21, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree.get('item', None), None)
        self.assertEqual(len(tree['children']), 0)

    def testAboveRoot(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/folder2')
        view = self.view_class(self.portal, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['item'].getPath(), '/plone/folder2/doc21')

    def testOutsideRoot(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root='/folder2')
        view = self.view_class(self.portal.folder1, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['item'].getPath(), '/plone/folder2/doc21')

    def testRootIsCurrent(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(currentFolderOnlyInNavtree=True)
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.assertEqual(tree['children'][0]['item'].getPath(), '/plone/folder2/doc21')

    def testCustomQuery(self):
        # Try a custom query script for the navtree that returns only published
        # objects
        workflow = self.portal.portal_workflow
        factory = self.portal.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript('getCustomNavQuery')
        script = self.portal.getCustomNavQuery
        script.ZPythonScript_edit('','return {"review_state":"published"}')
        self.assertEqual(self.portal.getCustomNavQuery(),{"review_state":"published"})
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))
        #Should only contain current object
        self.assertEqual(len(tree['children']), 1)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        #Should only contain current object and published folder
        self.assertEqual(len(tree['children']), 2)

    def testStateFiltering(self):
        # Test Navtree workflow state filtering
        workflow = self.portal.portal_workflow
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(wf_states_to_show=['published'])
        ntp.manage_changeProperties(enable_wf_state_filtering=True)
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        self.failUnless(tree)
        self.failUnless(tree.has_key('children'))
        #Should only contain current object
        self.assertEqual(len(tree['children']), 1)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        view = self.view_class(self.portal.folder2, self.request)
        tree = view.navigationTree()
        #Should only contain current object and published folder
        self.assertEqual(len(tree['children']), 2)

    

class TestCatalogNavTree(TestBaseNavTree):
        view_class = CatalogNavigationTree

class TestBaseSiteMap(PloneTestCase.PloneTestCase):
    """Tests for the sitemap view implementations. This base test is a little 
        geared toward a catalog based implementation for now.
    """

    view_class = None

    def afterSetUp(self):
        self.request = self.app.REQUEST
        # Apply a default layer for view lookups to work in Zope 2.9+
        setDefaultSkin(self.request)
        self.populateSite()
        
    def populateSite(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'doc1')
        self.portal.invokeFactory('Document', 'doc2')
        self.portal.invokeFactory('Document', 'doc3')
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Link', 'link1')
        self.portal.link1.setRemoteUrl('http://plone.org')
        self.portal.link1.reindexObject()
        folder1 = getattr(self.portal, 'folder1')
        folder1.invokeFactory('Document', 'doc11')
        folder1.invokeFactory('Document', 'doc12')
        folder1.invokeFactory('Document', 'doc13')
        self.portal.invokeFactory('Folder', 'folder2')
        folder2 = getattr(self.portal, 'folder2')
        folder2.invokeFactory('Document', 'doc21')
        folder2.invokeFactory('Document', 'doc22')
        folder2.invokeFactory('Document', 'doc23')
        folder2.invokeFactory('File', 'file21')
        self.setRoles(['Member'])

    def testCreateSitemap(self):
        view = self.view_class(self.portal, self.request)
        tree = view.siteMap()
        self.failUnless(tree)

    def testComplexSitemap(self):
        # create and test a reasonabley complex sitemap
        path = lambda x: '/'.join(x.getPhysicalPath())
        # We do this in a strange order in order to maximally demonstrate the bug
        folder1 = self.portal.folder1
        folder1.invokeFactory('Folder','subfolder1')
        subfolder1 = folder1.subfolder1
        folder1.invokeFactory('Folder','subfolder2')
        subfolder2 = folder1.subfolder2
        subfolder1.invokeFactory('Folder','subfolder11')
        subfolder11 = subfolder1.subfolder11
        subfolder1.invokeFactory('Folder','subfolder12')
        subfolder12 = subfolder1.subfolder12
        subfolder2.invokeFactory('Folder','subfolder21')
        subfolder21 = subfolder2.subfolder21
        folder1.invokeFactory('Folder','subfolder3')
        subfolder3 = folder1.subfolder3
        subfolder2.invokeFactory('Folder','subfolder22')
        subfolder22 = subfolder2.subfolder22
        subfolder22.invokeFactory('Folder','subfolder221')
        subfolder221 = subfolder22.subfolder221

        # Increase depth
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(sitemapDepth=5)

        view = self.view_class(self.portal, self.request)
        sitemap = view.siteMap()

        folder1map = sitemap['children'][6]
        self.assertEqual(len(folder1map['children']), 6)
        self.assertEqual(folder1map['item'].getPath(), path(folder1))

        subfolder1map = folder1map['children'][3]
        self.assertEqual(subfolder1map['item'].getPath(), path(subfolder1))
        self.assertEqual(len(subfolder1map['children']), 2)

        subfolder2map = folder1map['children'][4]
        self.assertEqual(subfolder2map['item'].getPath(), path(subfolder2))
        self.assertEqual(len(subfolder2map['children']), 2)

        subfolder3map = folder1map['children'][5]
        self.assertEqual(subfolder3map['item'].getPath(), path(subfolder3))
        self.assertEqual(len(subfolder3map['children']), 0)

        subfolder11map = subfolder1map['children'][0]
        self.assertEqual(subfolder11map['item'].getPath(), path(subfolder11))
        self.assertEqual(len(subfolder11map['children']), 0)

        subfolder21map = subfolder2map['children'][0]
        self.assertEqual(subfolder21map['item'].getPath(), path(subfolder21))
        self.assertEqual(len(subfolder21map['children']), 0)

        subfolder22map = subfolder2map['children'][1]
        self.assertEqual(subfolder22map['item'].getPath(), path(subfolder22))
        self.assertEqual(len(subfolder22map['children']), 1)

        # Why isn't this showing up in the sitemap
        subfolder221map = subfolder22map['children'][0]
        self.assertEqual(subfolder221map['item'].getPath(), path(subfolder221))
        self.assertEqual(len(subfolder221map['children']), 0)

    def testSitemapWithTopLevel(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1)
        view = self.view_class(self.portal, self.request)
        sitemap = view.siteMap()
        self.assertEqual(sitemap['children'][-1]['item'].getPath(), '/plone/folder2')
        
    def testSitemapWithBottomLevel(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(bottomLevel=1)
        view = self.view_class(self.portal, self.request)
        sitemap = view.siteMap()
        self.assertEqual(sitemap['children'][-1]['item'].getPath(), '/plone/folder2')
        self.failUnless(len(sitemap['children'][-1]['children']) > 0)
        
    def testSitemapWithNavigationRoot(self):
        ntp = self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(root = '/folder2')
        view = self.view_class(self.portal, self.request)
        sitemap = view.siteMap()
        self.assertEqual(sitemap['children'][-1]['item'].getPath(), '/plone/folder2/file21')

class TestSiteMap(TestBaseSiteMap):
        view_class = CatalogSiteMap

class TestBasePortalTabs(PloneTestCase.PloneTestCase):
    """Tests for the portal tabs view implementations
       This base test is a little geared toward a catalog based implementation
       for now.
    """

    view_class = None

    def afterSetUp(self):
        self.request = self.app.REQUEST
        setDefaultSkin(self.request)
        self.populateSite()

    def populateSite(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Document', 'doc1')
        self.portal.invokeFactory('Document', 'doc2')
        self.portal.invokeFactory('Document', 'doc3')
        self.portal.invokeFactory('Folder', 'folder1')
        self.portal.invokeFactory('Folder', 'folder2')
        self.setRoles(['Member'])

    def testCreateTopLevelTabs(self):
        # See if we can create one at all
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        #Only the folders show up (Members, news, events, folder1, folder2)
        self.assertEqual(len(tabs), 5)

    def testTabsRespectFolderOrder(self):
        # See if reordering causes a change in the tab order
        view = self.view_class(self.portal, self.request)
        tabs1 = view.topLevelTabs()
        # Must be manager to change order on portal itself
        self.setRoles(['Manager','Member'])
        self.portal.folder_position('up', 'folder2')
        view = self.view_class(self.portal, self.request)
        tabs2 = view.topLevelTabs()
        #Same number of objects
        self.failUnlessEqual(len(tabs1), len(tabs2))
        #Different order
        self.failUnless(tabs1 != tabs2)

    def testCustomQuery(self):
        # Try a custom query script for the tabs that returns only published
        # objects
        workflow = self.portal.portal_workflow
        factory = self.portal.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript('getCustomNavQuery')
        script = self.portal.getCustomNavQuery
        script.ZPythonScript_edit('', 'return {"review_state":"published"}')
        self.assertEqual(
            self.portal.getCustomNavQuery(), {"review_state":"published"})
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        #Should contain no folders
        self.assertEqual(len(tabs), 0)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        #Should only contain the published folder
        self.assertEqual(len(tabs), 1)

    def testStateFiltering(self):
        # Test tabs workflow state filtering
        workflow = self.portal.portal_workflow
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(wf_states_to_show=['published'])
        ntp.manage_changeProperties(enable_wf_state_filtering=True)
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        #Should contain no folders
        self.assertEqual(len(tabs), 0)
        #change workflow for folder1
        workflow.doActionFor(self.portal.folder1, 'publish')
        self.portal.folder1.reindexObject()
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        #Should only contain the published folder
        self.assertEqual(len(tabs), 1)

    def testDisableFolderTabs(self):
        # Setting the site_property disable_folder_sections should remove
        # all folder based tabs
        props = self.portal.portal_properties.site_properties
        props.manage_changeProperties(disable_folder_sections=True)
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.assertEqual(tabs, [])

    def testTabsExcludeItemsWithExcludeProperty(self):
        # Make sure that items witht he exclude_from_nav property are purged
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        orig_len = len(tabs)
        self.portal.folder2.setExcludeFromNav(True)
        self.portal.folder2.reindexObject()
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        self.assertEqual(len(tabs), orig_len - 1)
        tab_names = [t['id'] for t in tabs]
        self.failIf('folder2' in tab_names)

    def testTabsRespectsTypesWithViewAction(self):
        # With a type in typesUseViewActionInListings as current action it
        # should return a tab which has '/view' appended to the url
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        # Fail if 'view' is used for folder
        self.failIf(tabs[-1]['url'][-5:]=='/view')
        # Add Folder to site_property
        props = self.portal.portal_properties.site_properties
        props.manage_changeProperties(
            typesUseViewActionInListings=['Image','File','Folder'])
        # Verify that we have '/view'
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        self.assertEqual(tabs[-1]['url'][-5:],'/view')

    def testTabsExcludeItemsInIdsNotToList(self):
        # Make sure that items whose ids are in the idsNotToList navTree
        # property get purged
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        orig_len = len(tabs)
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(idsNotToList=['folder2'])
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        self.assertEqual(len(tabs), orig_len - 1)
        tab_names = [t['id'] for t in tabs]
        self.failIf('folder2' in tab_names)

    def testTabsExcludeNonFolderishItems(self):
        # Make sure that items witht he exclude_from_nav property are purged
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        orig_len = len(tabs)
        self.setRoles(['Manager','Member'])
        self.portal.invokeFactory('Document','foo')
        self.portal.foo.reindexObject()
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        self.assertEqual(len(tabs),orig_len)

    def testRootBelowPortalRoot(self):
        
        self.setRoles(['Manager'])
        self.portal.folder1.invokeFactory('Document', 'doc1')
        self.portal.folder1.invokeFactory('Document', 'doc2')
        self.portal.folder1.invokeFactory('Document', 'doc3')
        self.portal.folder1.invokeFactory('Folder', 'folder1')
        self.portal.folder1.invokeFactory('Folder', 'folder2')
        self.setRoles(['Member'])
        
        rootPath = '/'.join(self.portal.getPhysicalPath()) + '/folder1'
        self.portal.portal_properties.navtree_properties.root = '/folder1'
        
        view = self.view_class(self.portal, self.request)
        tabs = view.topLevelTabs()
        self.failUnless(tabs)
        self.assertEqual(len(tabs), 2)
        self.assertEqual(tabs[0]['id'], 'folder1')
        self.assertEqual(tabs[1]['id'], 'folder2')
        

class TestCatalogPortalTabs(TestBasePortalTabs):
        view_class = CatalogNavigationTabs


class TestBaseBreadCrumbs(PloneTestCase.PloneTestCase):
    """Tests for the portal tabs query
    """

    view_class = None

    def afterSetUp(self):
        self.request = self.app.REQUEST
        setDefaultSkin(self.request)
        self.populateSite()

    def populateSite(self):
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Folder', 'folder1')
        folder1 = getattr(self.portal, 'folder1')
        folder1.invokeFactory('Document', 'doc11')
        folder1.invokeFactory('File', 'file11')
        self.setRoles(['Member'])

    def testCreateBreadCrumbs(self):
        # See if we can create one at all
        doc = self.portal.folder1.doc11
        view = self.view_class(doc, self.request)
        crumbs = view.breadcrumbs()
        self.failUnless(crumbs)
        self.assertEqual(len(crumbs), 2)
        self.assertEqual(crumbs[-1]['absolute_url'], doc.absolute_url())
        self.assertEqual(crumbs[-2]['absolute_url'], doc.aq_parent.absolute_url())

    def testBreadcrumbsRespectTypesWithViewAction(self):
        # With a type in typesUseViewActionInListings as current action it
        # should return a breadcrumb which has '/view' appended to the url
        file = self.portal.folder1.file11
        view = self.view_class(self.portal.folder1.file11, self.request)
        crumbs = view.breadcrumbs()
        self.failUnless(crumbs)
        self.assertEqual(crumbs[-1]['absolute_url'][-5:],'/view')
        
    def testBreadcrumbsStopAtNavigationRoot(self):
        ntp=self.portal.portal_properties.navtree_properties
        ntp.manage_changeProperties(topLevel=1, root='/folder1')
        view = self.view_class(self.portal.folder1.doc11, self.request)
        crumbs = view.breadcrumbs()
        self.failUnless(crumbs)
        self.assertEqual(crumbs[0]['absolute_url'], self.portal.folder1.doc11.absolute_url())


class TestCatalogBreadCrumbs(TestBaseBreadCrumbs):
    view_class = CatalogNavigationBreadcrumbs


class TestPhysicalBreadCrumbs(TestBaseBreadCrumbs):
    view_class = PhysicalNavigationBreadcrumbs

    def testBreadcrumbsFilterByInterface(self):
        view = self.view_class(self.portal.folder1.doc11, self.request)
        crumbs = view.breadcrumbs()
        directlyProvides(self.portal.folder1, IHideFromBreadcrumbs)
        newcrumbs = view.breadcrumbs()
        self.assertEqual(len(crumbs)-1, len(newcrumbs))
        self.assertEqual(newcrumbs[0]['absolute_url'], self.portal.folder1.doc11.absolute_url())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCatalogPortalTabs))
    suite.addTest(makeSuite(TestCatalogNavTree))
    suite.addTest(makeSuite(TestSiteMap))
    suite.addTest(makeSuite(TestCatalogBreadCrumbs))
    suite.addTest(makeSuite(TestPhysicalBreadCrumbs))
    return suite

if __name__ == '__main__':
    framework()