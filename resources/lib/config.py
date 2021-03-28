#!/usr/bin/python
#
# CONFIG FILE
#
#Modules necessaires : IrcLib / BeautifulSoup / Python2.X
#
# all options and parameters for your implementation of
# this project are here
#

# IRC bot
# from xbmcswift2 import Plugin
from kodiswift import Plugin

plugin=Plugin()
ircDefaultChannel = "#test"
ircDefaultNickname = "Gunther"
ircDefaultServer = "irc.freenode.net"
ircDefaultNumPaquet = 1
ircDefaultNomRobot = "Grabator"
ircDefaultSecondChannel = ""
ircDefaultPort = 6667
ircDefaultVersion = "HexChat 2.9.5"
ircTempoAvantDL = 5.2

# Search parameters
defaultUrl = "http://ixirc.com/?q="

# Downloads
downloadPath = plugin.get_setting('xg_dl_path')
