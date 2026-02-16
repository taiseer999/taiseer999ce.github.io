# -*- coding: utf-8 -*-

import xbmc
import xbmcgui

KodiFont = xbmc.getInfoLabel('Skin.Font')

xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skintheme","value":"Perfect Pink"}}')
xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.skincolors","value":"Perfect Pink"}}')

if KodiFont:
    xbmc.executeJSONRPC('{"jsonrpc":"2.0","method":"Settings.SetSettingValue","id":1,"params":{"setting":"lookandfeel.font","value":"'+KodiFont+'"}}')

try:
    are_you_sure = xbmcgui.Dialog().yesno("Confluence ZEITGEIST","Color scheme has been set to \"Perfect Pink\"[CR][CR]Changing your background to the matching[CR]\"Frosted Glass · Perfect Pink\"     Continue?  [LIGHT](Recommended)[/LIGHT]")
    if are_you_sure:
        xbmc.executebuiltin('Skin.SetString(UseCustomBackground,)')
        xbmc.executebuiltin('Skin.SetString(BackgroundDarkenStrength,1)')
        xbmc.executebuiltin('Skin.SetString(BackgroundType,14)')
    xbmc.executebuiltin('SetFocus(109)')
except:
    pass