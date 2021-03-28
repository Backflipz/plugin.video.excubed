from __future__ import absolute_import
import os.path

import irc.client
import irc.buffer
from irc.bot import SingleServerIRCBot
from io import open
import xbmc
irc.client.ServerConnection.buffer_class = irc.buffer.LenientDecodingLineBuffer
import shlex


def parse_args(e, tpl):
    result = list()
    src = e.source
    append = result.append
    if len(e.arguments) == 2:
        args = e.arguments[:1] + e.arguments[1].split()
    else:
	    args = e.arguments
    args = shlex.split(args)    
    l = len(args)
    print "ARGS %s" % args    
    xbmc.log(args)
    for i in tpl:
        print str(args)
        if l >= 1 and i == u"protocol":
            append(args[0])
        elif l >= 2 and i == u"opt":
            append(args[1])
        elif l >= 3 and i == u"filename":
            append(args[2])
        elif l >= 4 and i == u"ip":
            print args[3]
            append(irc.client.ip_numstr_to_quad(args[3]))
        elif l >= 5 and i == u"port":
            append(int(args[3]))
        elif i == u"name":
            append(irc.client.nm_to_n(src))
        else:
            return
            
    return result

class XDCC(SingleServerIRCBot):
    def __init__(self, nick, address, port, channels, task,
                 download_dir = u"."):
        
        SingleServerIRCBot.__init__(self, [(address, port)],
                                    nick, nick)

        self.__recv_bytes = 0
        self.task = task
        self.filepath = u""
        self.download_dir = download_dir
        self.chans = channels
        self.file = None
        self.dcc = None
        
    def get_version(self):
        return u"tvxdcc"
    
    def on_welcome(self, c, e):
        for i in self.chans:
            c.join(i)
        
    def on_join(self, c, e):
        self.request_file(*self.task)

    def on_privmsg(self, c, e):
        pass

    def on_ctcp(self, c , e):
        xbmc.log(e.arguments)
        args = parse_args(e, (u"protocol", u"opt", u"filename",
                              u"ip", u"port"))
        
        if not args or args[0:2] not in ([u"XDCC", u"SEND"],
                                         [u"DCC", u"SEND"]):
            
            return SingleServerIRCBot.on_ctcp(self, c, e)

        self.filepath = os.path.join(self.download_dir, args[2])
        self.file = open(self.filepath, u"ab")
        self.dcc = self.dcc_connect(* args[3:5]+[u"raw"] )
        print u"\ndownload started"

    def on_dccmsg(self, c, e):
        u"""Called by Reactor pattern"""
        data = e.arguments[0]  #don't use parse_args here
        self.file.write(data)    
        self.__recv_bytes += len(data)
        #print("received", len(data), "bytes of data")
        #self.dcc.privmsg(str(self.__recv_bytes))

    def on_dcc_disconnect(self, c, e):
        print u"\nconnexion lost"
        print u"Resending request message.."
        self.file.close()
        self.request_file(*self.task)

    def request_file(self, botname, num):
        msg = u"xdcc send #" + unicode(num)
        self.connection.privmsg(botname, msg)





                          
