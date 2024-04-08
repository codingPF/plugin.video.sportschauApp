# -*- coding: utf-8 -*-
# SPDX-License-Identifier: MIT
"""
The base logger module
"""
from .singleton import Singleton

class AppContext(Singleton):
    LOGGER = None
    SETTINGS = None
    ADDONCLASS = None
    
    def __init__(self):
        None

    def initAddon(self, aAddon):
        self.ADDONCLASS = aAddon
    
    def initLogger(self, aLogger):
        self.LOGGER = aLogger
    
    
    def initSettings(self, aSettings):
        self.SETTINGS = aSettings
