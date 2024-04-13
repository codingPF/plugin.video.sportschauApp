# -*- coding: utf-8 -*-
"""
The main addon module

SPDX-License-Identifier: MIT

"""
import xbmcplugin
import time
import os
import resources.lib.fw.utils as pyUtils
import resources.lib.fw.kodiUi as KodiUI
from resources.lib.fw.kodi import Kodi
import resources.lib.fw.kodiProgressDialog as PG
import resources.lib.dpSportschau as dps
#


class Main(Kodi):

    def __init__(self):
        super(Main, self).__init__()
        self.logger = self.createLogger('Main')

    def run(self):
        #
        mode = self.getParameters('mode')
        self.logger.info('Run Plugin with Parameters {}', self.getParameters())
        # if mode == 'organization':
        if mode == 'A':
            mmUI = KodiUI.KodiUI(self)
            href = self.getParameters('urlB64')
            self.genSub(mmUI, dps.DpSportschau(self).getSub(pyUtils.b64decode(href)))
        elif mode == 'B':
            mmUI = KodiUI.KodiUI(self)
            href = self.getParameters('urlB64')
            self.genSub(mmUI, dps.DpSportschau(self).getPage(pyUtils.b64decode(href)))
        else:
            mmUI = KodiUI.KodiUI(self)
            self.genMenu(mmUI, dps.DpSportschau(self).getRoot())
        

    ##########
    
    def genMenu(self, pUI, pData):
        for element in pData:
            #
            self.logger.info('genMenu {}', element)
            
            targetUrl = pyUtils.build_url({
                'mode': 'A',
                'urlB64' : pyUtils.b64encode(element['href'])
                })
            pUI.addDirectoryItem(
                pTitle=element['name'],
                pUrl=targetUrl
            )
        #
        pUI.render()

    def genSub(self, pUI, pData):
        uData = pyUtils.makeDictUnique(pData)
        for element in uData:
            #
            self.logger.info('genSub {}', element)
            name = element['name']
            if "topTitle" in element and element["topTitle"] != None:
                name = "(" + element["topTitle"] + ") " + name
            if element['type'] == 'P' :
                pUI.addListItem(
                    pTitle=name,
                    pUrl=element['href'],
                    pPlot=element['description'],
                    pIcon=element['image'],
                    pAired=element['pubDate'],
                    pDuration=element['duration']
                )
            else:
                targetUrl = pyUtils.build_url({
                    'mode': 'B',
                    'urlB64' : pyUtils.b64encode(element['href'])
                })
                pUI.addDirectoryItem(
                    pTitle=name,
                    pUrl=targetUrl
                )
            
            #def addDirectoryItem(self, pTitle, pUrl, pSortTitle = None, pIcon = None, pContextMenu = None):
            #addListItem(self, pTitle, pUrl, pSortTitle = None, pPlot = None, pDuration = None, pAired = None, pIcon = None, pContextMenu = None, pPlayable = 'True', pFolder = False):

        #
        pUI.render()

