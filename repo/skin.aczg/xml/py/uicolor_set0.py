# -*- coding: utf-8 -*-

import xbmc
import xbmcgui

KodiFont = xbmc.getInfoLabel('Skin.Font')

xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skintheme","value":"SKINDEFAULT"}}')
xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skincolors","value":"SKINDEFAULT"}}')

if KodiFont:
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"'+KodiFont+'"}}')

try:
    are_you_sure = xbmcgui.Dialog().yesno("Confluence ZEITGEIST","Color scheme has been set to \"Kodi Blue\"  [LIGHT](Default)[/LIGHT][CR][CR]Changing your background to the matching[CR]\"Frosted Glass · Light Colors\"     Continue?  [LIGHT](Recommended)[/LIGHT]")
    if are_you_sure:
        xbmc.executebuiltin('Skin.SetString(UseCustomBackground,)')
        xbmc.executebuiltin('Skin.SetString(BackgroundDarkenStrength,1)')
        xbmc.executebuiltin('Skin.SetString(BackgroundType,)')
    xbmc.executebuiltin('SetFocus(109)')
except:
    pass