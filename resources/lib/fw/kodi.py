# -*- coding: utf-8 -*-
"""
Kodi Interface

SPDX-License-Identifier: MIT
"""
import sys
import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
import xbmcaddon
try:
    # Python 3.x
    from urllib.parse import urlencode
    from urllib.parse import parse_qs
except ImportError:
    # Python 2.x
    from urllib import urlencode
    from urlparse import parse_qs
    
from resources.lib.fw.singleton import Singleton
from resources.lib.fw.logger import Logger
import resources.lib.fw.utils as pyUtils
import resources.lib.fw.kodiProgressDialog as PG

class Kodi(Singleton):

    def __init__(self):
        self._addonClass = xbmcaddon.Addon()
        self._addonUrl = sys.argv[0]
        self._addon_handle = int(sys.argv[1])
        self._parameter = parse_qs(sys.argv[2][1:])
        self.log = Logger(self._addonClass.getAddonInfo('id'), self._addonClass.getAddonInfo('version'), 'Kodi')
        self._progressDialog = PG.KodiProgressDialog(self)
        self._localizeString = self._addonClass.getLocalizedString
        # we do store last access for later use
        import time
        self._lastUsed = self.getSetting("LastUsed", 0)
        self.setSetting("LastUsed", str(int(time.time())));

    ## Wrap settings
    def setSetting(self, setting_id, value):
        return self._addonClass.setSetting(setting_id, value)

    def getSetting(self, setting_id, defaultValue=None):
        value = pyUtils.py2_decode(self._addonClass.getSetting(setting_id))
        if value is None and defaultValue is not None:
            return defaultValue
        return value

    ## General Plugin info
    def getAddonDataPath(self):
        return self.translatePath(self._addonClass.getAddonInfo('profile'))

    def getAddonPath(self):
        return pyUtils.py2_decode(self._addonClass.getAddonInfo('path'))
    
    ## kodi helper
    def getKodiVersion(self):
        """
        Get Kodi major version
        Returns:
            int: Kodi major version (e.g. 18)
        """
        xbmc_version = xbmc.getInfoLabel("System.BuildVersion")
        return int(xbmc_version.split('-')[0].split('.')[0])

    def translatePath(self, pPath):
        path = pyUtils.py2_decode(pPath)
        if self.getKodiVersion() > 18:
            return pyUtils.py2_decode(xbmcvfs.translatePath(path))
        else:
            return pyUtils.py2_decode(xbmc.translatePath(path))

    def localizeString(self, pParam):
        rt = self._localizeString(pParam)
        if rt == '':
            rt = str(pParam)
        return rt
    
    def getAddonHandle(self):
        return self._addon_handle
    
    ## wrappers
    def createLogger(self, topic=None):
        return self.log.getInstance(topic)
    
    def getProgressDialog(self):
        return self._progressDialog

    def executebuiltin(self, builtin):
        xbmc.executebuiltin(builtin)
    
    def getAbortHook(self):
        return xbmc.Monitor().abortRequested
    
    ## Other wrappers
    def getParameters(self, pName=None, default=None):
        if pName == None:
            return self._parameter
        try:
            argument = self._parameter[pName][0]
            argument = pyUtils.py2_decode(argument)
            return argument
        except TypeError:
            return default
        except KeyError:
            return default

    def generateUrl(self, params):
        """
        Builds a valid plugin url passing the supplied
        parameters object

        Args:
            params(object): an object containing parameters
        """
        if params == None:
            return self._addonUrl
        # BUG in urlencode which is solved in python 3
        utfEnsuredParams = pyUtils.dict_to_utf(params)
        return self._addonUrl + '?' + urlencode(utfEnsuredParams)

    def playItem(self, pUrl, pSubTitle=None):

        if self.getKodiVersion() > 17:
            listitem = xbmcgui.ListItem(path=pUrl, offscreen=True)
        else:
            listitem = xbmcgui.ListItem(path=pUrl)

        listitem.setProperty('IsPlayable', 'true')

        if pSubTitle is not None:
            listitem.setSubtitles(pSubTitle)

        xbmcplugin.setResolvedUrl(self._addon_handle, True, listitem)

    ## skin stuff
    def getSkinName(self):
        return xbmc.getSkinDir();

    def getCurrentViewId(self):
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        return window.getFocusId()

    def setViewId(self, viewId):
        if viewId > -1:
            xbmc.sleep(10)
            self.executebuiltin('Container.SetViewMode({})'.format(viewId))
            self.executebuiltin('Container.SetViewMode({})'.format(viewId))

###############################################################

    def resolveViewId(self, pViewname):
        skinName = self.getSkinName()
        viewId = -1
        # skin.estuary
        skinEstuary = 'skin.estuary'
        skinEstouchy = 'skin.estouchy'
        skinConfluence = 'skin.confluence'
        #
        viewMain = 'MAIN'
        viewShow = 'SHOWS'
        viewList = 'LIST'
        viewThump = 'THUMBNAIL'
        #
        if skinName == skinEstuary:
            if pViewname == viewMain:
                viewId = 55
            elif pViewname == viewShow:
                viewId = 55
            elif pViewname == viewList:
                viewId = 55
            elif pViewname == viewThump:
                viewId = 500
        elif skinName == skinEstouchy:
            if pViewname == viewMain:
                viewId = 500
            elif pViewname == viewShow:
                viewId = 500
            elif pViewname == viewList:
                viewId = 550
            elif pViewname == viewThump:
                viewId = 55
        elif skinName == skinConfluence:
            if pViewname == viewMain:
                viewId = 51
            elif pViewname == viewShow:
                viewId = 51
            elif pViewname == viewList:
                viewId = 504
            elif pViewname == viewThump:
                viewId = 500
        #
        self.logger.debug('proposed view id {} for {} in mode {}', viewId, skinName, pViewname)
        return viewId;

##############################################################

    def get_entered_text(self, deftext=None, heading=None, hidden=False):
        """
        Asks the user to enter a text. The method returnes a tuple with
        the text and the confirmation status: `( "Entered Text", True, )`

        Args:
            deftext(str|int, optional): Default text in the text entry box.
                Can be a string or a numerical id to a localized text. This
                text will be returned if the user selects `Cancel`

            heading(str|int, optional): Heading text of the text entry UI.
                Can be a string or a numerical id to a localized text.

            hidden(bool, optional): If `True` the entered text is not
                desplayed. Placeholders are used for every char. Default
                is `False`
        """
        heading = self.localizeString(heading) if isinstance(heading, int) else heading if heading is not None else ''
        deftext = self.localizeString(deftext) if isinstance(deftext, int) else deftext if deftext is not None else ''
        keyboard = xbmc.Keyboard(deftext, heading, 1 if hidden else 0)
        keyboard.doModal()
        if keyboard.isConfirmed():
            enteredText = keyboard.getText();
            enteredText = pyUtils.py2_decode(enteredText);
            return (enteredText, True, )
        return (deftext, False, )
