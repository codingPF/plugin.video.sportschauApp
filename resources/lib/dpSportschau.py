# -*- coding: utf-8 -*-
"""
The local SQlite database module
SPDX-License-Identifier: MIT
"""

# pylint: disable=too-many-lines,line-too-long
import json
import datetime
import time
from resources.lib.appContext import AppContext
import resources.lib.utils as pyUtils
import resources.lib.kodiProgressDialog as PG
import resources.lib.webResource as WebResource
import hashlib
import xml.etree.ElementTree as ET

class DpSportschau(object):
    """
    RefreshArdAudiothek
    """

    def __init__(self, pAbortHook):
        self.logger = AppContext().LOGGER.getInstance('DpSportschau')
        self.settings = AppContext().SETTINGS
        self.abortHook = pAbortHook        
        self.kodiPG = None
        self.starttime = time.time()
        #
        self.apiUrlMenu = 'https://exporte.wdr.de/SportschauNextServer/menu';
        #

    def _loadUrl(self, pUrl, pAge = 3600):
        self.logger.debug('load url {}', pUrl)
        kkey = self.settings.getDatapath() + hashlib.md5(pUrl.encode()).hexdigest() + ".cache"
        if pyUtils.file_exists(kkey):
            try:
                self.logger.debug('cache read {}', kkey)
                cData = pyUtils.loadJson(kkey)
                if cData.get('cTime') + pAge > int(time.time()):
                    self.logger.debug('cache read is valid')
                    return pyUtils.b64decode(cData.get('data'))
            except Exception as err:
                self.logger.error('_loadUrl {}', err)
        self.logger.debug('cache build {}', kkey)
        dn = WebResource.WebResource(pUrl, pProgressListener=self.kodiPG.updateProgress, pAbortHook=self.abortHook)
        dataString = dn.retrieveAsString()
        cData = { 'cTime': int(time.time()) , 'url' : pUrl, 'data' : pyUtils.b64encode( dataString.decode('utf-8')) }
        pyUtils.saveJson(kkey, cData)
        self.logger.debug('cache write {}', kkey)
        return pyUtils.b64decode(cData.get('data'))

    def getRoot(self):
        self.logger.debug('getRoot')
        rs = []
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30003)
        try:
            url = self.apiUrlMenu
            self.logger.debug('url {}',url)
            data = json.loads(self._loadUrl(url))
            rootItems = pyUtils.extractJsonValue(data, 'items')
            if rootItems:
                categoryItems = pyUtils.extractJsonValue(rootItems, 1, 'items')
                for item in categoryItems:
                    rs.append(self._processItem(item))
        except Exception as err:
            self.logger.error('getRoot {}', err)
            raise
        self.kodiPG.close()
        return rs
        
    
    def _processItem(self, pItem):
        rs = {
            'url': pyUtils.extractJsonValue(pItem, 'url'),
            'name': pyUtils.extractJsonValue(pItem, 'name'),
            'path': pyUtils.extractJsonValue(pItem, 'path'),
            'pos': pyUtils.extractJsonValue(pItem, 'position'),
            'type': pyUtils.extractJsonValue(pItem, '_links', 'target', 'type'),
            'href': pyUtils.extractJsonValue(pItem, '_links', 'target', 'href')
            }
        self.logger.debug('_processItem {}',rs)
        return rs

    def getSub(self, pUrl):
        self.logger.debug('getSub')
        rs = []
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30003)
        try:
            self.logger.debug('url {}',pUrl)
            data = json.loads(self._loadUrl(pUrl))
            subCategories = pyUtils.extractJsonValue(data, 'subCategories')
            if subCategories:
                for item in subCategories:
                    rs.append(self._processSubcategory(pyUtils.extractJsonValue(item, '_links', 'target')))
            #
            items = pyUtils.extractJsonValue(data, 'items')
            rs += self._processItemsTeasters(items)
            
        except Exception as err:
            self.logger.error('getSub {}', err)
            raise
        self.kodiPG.close()
        return rs

    def _processSubcategory(self, pItem):
        rs = {
            'name': pyUtils.extractJsonValue(pItem, 'title'),
            'type': 'C',#pyUtils.extractJsonValue(pItem, 'type'),
            'href': pyUtils.extractJsonValue(pItem, 'href')
            }
        self.logger.debug('_processSubcategory {}',rs)
        return rs

    def _processTeaser(self, pItem):
        videoUrls = pyUtils.extractJsonValue(pItem, 'app', 'playerMediaCollection')
        jsonVideoElement = json.loads(videoUrls)
        rs = {
            'name': pyUtils.extractJsonValue(pItem, 'title'),
            'pubDate': (pyUtils.extractJsonValue(pItem, 'pubDate')/1000),
            'duration': int(pyUtils.extractJsonValue(pItem, 'app', 'duration')),
            'date': pyUtils.extractJsonValue(pItem, 'app', 'beitragszeit'),
            'type': 'P', #pyUtils.extractJsonValue(pItem, 'dokumenttyp'),
            'description': pyUtils.extractJsonValue(pItem, 'description'),
            'image': pyUtils.extractJsonValue(pItem, 'image', 'images', 0, 'imageUrl'),
            #'href': pyUtils.extractJsonValue(jsonVideoElement, 'streams', 0, 'media', 0, 'url')
            'href': self._extractVideo(jsonVideoElement)
            }
        self.logger.debug('_processTeaser {}',rs)
        return rs

    def _processTopMediaType(self, pItem):
        avLink = pyUtils.extractJsonValue(pItem, 'app', 'avlink')
        # parse xml
        tree = ET.ElementTree(ET.fromstring(self._loadUrl(avLink)))
        ns = {'app' : 'http://www.wdr.de/rss/1.0/modules/app/1.0/' , 'mp' : 'http://www.wdr.de/rss/1.0/modules/mp' }
        root = tree.getroot()
        
        self.logger.debug('item title {}', tree.find('.//item/title').text)
        self.logger.debug('item app:stand {}', tree.find('.//item/app:stand', ns).text)
        #self.logger.debug('item description {}', tree.find('.//item/description').text)
        #self.logger.debug('item duration {}', tree.find('.//item/app:duration', ns).text)
        #self.logger.debug('item playerMediaCollection {}', tree.find('.//item/app:playerMediaCollection', ns).text)
        self.logger.debug('item image {}', tree.find('.//item/mp:image/mp:data', ns).text)
        
        jsonVideoElement = json.loads(tree.find('.//item/app:playerMediaCollection', ns).text)
        epoch = pyUtils.epoch_from_timestamp( tree.find('.//item/app:stand', ns).text, '%Y-%m-%dT%H:%M:%S %z')
        description = tree.find('.//item/description') or tree.find('.//channel/description')
        rs = {
            'name': tree.find('.//item/title').text,
            'pubDate': epoch,
            'duration': int(tree.find('.//item/app:duration', ns).text),
            'date': epoch,
            'type': 'P',
            'description': description.text,
            'image': tree.find('.//item/mp:image/mp:data', ns).text,
            #'href': pyUtils.extractJsonValue(jsonVideoElement, 'streams', 0, 'media', 0, 'url')
            'href': self._extractVideo(jsonVideoElement)
            }
        self.logger.debug('_processTopMediaType {}',rs)
        return rs
    
    def getPage(self, pUrl):
        self.logger.debug('getPage')
        rs = []
        self.kodiPG = PG.KodiProgressDialog()
        self.kodiPG.create(30003)
        try:
            self.logger.debug('url {}',pUrl)
            data = json.loads(self._loadUrl(pUrl))
            simpleMenu = pyUtils.extractJsonValue(data, 'content', 'item', 0, '_links', 'news', 'href')
            #
            if simpleMenu:
                self.logger.debug('simpleMenu[0] url {}', simpleMenu)
                data = json.loads(self._loadUrl(simpleMenu))
                
            items = pyUtils.extractJsonValue(data, 'items')
            rs += self._processItemsTeasters(items)
                                    
            
        except Exception as err:
            self.logger.error('getPage {}', err)
            raise
        self.kodiPG.close()
        return rs

    def _processItemsTeasters(self, items):
        rs = []
        topTitle = None
        if items:
            self.logger.debug('items')
            for item in items:
                self.logger.debug('item')
                topTitle = pyUtils.extractJsonValue(item, 'title') or topTitle
                teasers = pyUtils.extractJsonValue(item, 'teasers')
                if teasers:
                    self.logger.debug('teasers')
                    for teaser in teasers:
                        dokumenttyp = pyUtils.extractJsonValue(teaser, 'dokumenttyp')
                        topMediaType = pyUtils.extractJsonValue(teaser, 'topMediaType')
                        mediaType = pyUtils.extractJsonValue(teaser, 'mediaCategory')
                        self.logger.debug('teaser title: {} dokumenttyp: {} topMediaType: {}', topTitle, dokumenttyp, topMediaType)
                        try:
                            if dokumenttyp == 'video' or mediaType == 'video':
                                tData = self._processTeaser(teaser)
                                tData['topTitle'] = topTitle
                                rs.append(tData)
                            elif topMediaType == 'video':
                                tData = self._processTopMediaType(teaser)
                                tData['topTitle'] = topTitle
                                rs.append(tData)
                        except Exception as err:
                            self.logger.error('getPage _processTeaser / _processTopMediaType {}', err)
        return rs

    def _extractVideo(self, pItem):
        urls = pyUtils.extractJsonValue(pItem, 'streams', 0, 'media')
        byResolution = []
        for url in urls:
            px = pyUtils.extractJsonValue(url, 'maxHResolutionPx') 
            u = pyUtils.extractJsonValue(url, 'url')
            byResolution.append({'px':px,'url':u})
        
        sortedUrls = sorted(byResolution, key=lambda x: tuple(sorted(x.keys())))
        theOne = sortedUrls[0]['url']
        self.logger.debug('_extractVideo: {} of {}', theOne, sortedUrls)
        return theOne
