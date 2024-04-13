# -*- coding: utf-8 -*-
"""
Kodi Interface to progress dialog

SPDX-License-Identifier: MIT
"""
import xbmcgui
import xbmc


class KodiProgressDialog(object):
    """ Kodi Progress Dialog Class """

    def __init__(self, pAddon):
        self._addon = pAddon
        self.logger = pAddon.createLogger('KodiProgressDialog')
        self.pgdialog = None
        self.lastProgress = 0

    def __del__(self):
        self.close()

    def create(self, heading=30003, message=None):
        """
        Shows a progress dialog to the user

        Args:
            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        heading = self._addon.localizeString(heading) if isinstance(heading, int) else heading
        message = self._addon.localizeString(message) if isinstance(message, int) else message
        if self.pgdialog is None:
            self.pgdialog = xbmcgui.DialogProgressBG()
            self.pgdialog.create(heading, message)
        else:
            self.pgdialog.update(0, heading, message)
            self.lastProgress = 0

    def update(self, percent, heading=None, message=None):
        """
        Updates a progress dialog

        Args:
            percent(int): percentage of progress

            heading(str|int): Heading text of the progress dialog.
                Can be a string or a numerical id to a localized text.

            message(str|int): Text of the progress dialog.
                Can be a string or a numerical id to a localized text.
        """
        if self.pgdialog is not None:
            heading = self._addon.localizeString(heading) if isinstance(heading, int) else heading
            message = self._addon.localizeString(message) if isinstance(message, int) else message
            if self.lastProgress+9 < percent:
                self.pgdialog.update(percent, heading, message)
                self.lastProgress = percent
                self.logger.debug('update progress {}', percent)

    def updateProgress(self, pDone, pTotal):
        self.update( int( (pDone / ( pTotal * 1.0 ) ) * 100 ) )

    def close(self):
        """ Closes a progress dialog """
        if self.pgdialog is not None:
            self.pgdialog.close()
            del self.pgdialog
            self.pgdialog = None

    def startBussyDialog(self):
        self._addon.executebuiltin("ActivateWindow(busydialog)")

    def stopBussyDialog(self):
        self._addon.executebuiltin("Dialog.Close(busydialog)")
