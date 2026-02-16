# -*- coding: utf-8 -*-

import xbmc
import xbmcgui

KodiFont = xbmc.getInfoLabel('Skin.Font')

xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skintheme","value":"Electric Violet"}}')
xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skincolors","value":"Electric Violet"}}')

if KodiFont:
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"'+KodiFont+'"}}')

try:
    are_you_sure = xbmcgui.Dialog().yesno("Confluence ZEITGEIST","Color scheme has been set to \"Electric Violet\"[CR][CR]Changing your background to the matching[CR]\"Frosted Glass · Electric Violet\"     Continue?  [LIGHT](Recommended)[/LIGHT]")
    if are_you_sure:
        xbmc.executebuiltin('Skin.SetString(UseCustomBackground,)')
        xbmc.executebuiltin('Skin.SetString(BackgroundDarkenStrength,1)')
        xbmc.executebuiltin('Skin.SetString(BackgroundType,15)')
    xbmc.executebuiltin('SetFocus(109)')
except:
    pass