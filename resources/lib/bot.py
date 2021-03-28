#!/usr/bin/python
# -*- coding: utf8 -*-

## POUR DCCRECEIVE ?
#from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import os
import struct
import irc.bot
import irc.strings
#from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
from config import *
import re
import random
from io import open
import shlex

def download(connection, nomRobot, numPaquet):
    print u"commande XDCC SEND #" + unicode(numPaquet)
    connection.notice(nomRobot, u"xdcc send #" + unicode(numPaquet) )

def checkTerminated(bot, DL):
    if DL.terminated == True :
        bot.die()

################################################################################
# CLASS Grabator
################################################################################    
class Grabator(irc.bot.SingleServerIRCBot):
    u"""
        class Grabator
        
        definit un bot qui se connecte a un serveur irc et est capable de 
        telecharger des paquets en xdcc.
        Il peut scanner le topic du channel principal ainsi que les messages
        prives afin de se connecter aux salons et channels de chat.
    
    """
    def __init__(
            self, 
            objetDL,
            channel = ircDefaultChannel, 
            nickname = ircDefaultNickname, 
            server = ircDefaultServer, 
            numPaquet = ircDefaultNumPaquet, 
            nomRobot = ircDefaultNomRobot, 
            secondChannel = ircDefaultSecondChannel,
            port = ircDefaultPort
            ):
        print u"channel =", channel, u"; nickname =", nickname, u"; server = ", server, port #DEBUG
        try:
            irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        except:
            print u"bot.py : pb creation bot/connexion server"
        self.objetDL = objetDL
        self.channel = channel
        self.numPaquet = numPaquet
        self.nomRobot = nomRobot
        self.secondChannel = secondChannel
        self.received_bytes = 0
        self.ctcp_version = ircDefaultVersion
        self.repriseDL = False
        self.position = 0
        # Pour gerer les encodages :
        self.connection.buffer_class.encoding = u'utf-8'# self.connection.buffer_class. = irc.buffer.LineBuffer
        # Execution retardee de l'envoi de la commande SEND (permettre connexion au second channel)
        self.connection.execute_every(0.5, checkTerminated, (self, self.objetDL ) )
        
    # def on_nicknameinuse(self, c, event):
        # c.nick(c.get_nickname() + u"_")
        
    def on_welcome(self, connection, event):
        connection.join(self.channel)
        
        # pour gerer les probleme d'encodage
        self.connection.buffer.errors = u'replace'
        
        if (self.secondChannel != u""):
            print u"connexion au secondChannel :", self.secondChannel
            connection.join(self.secondChannel)
        
        # tempo et commande pour telechargement
        connection.execute_delayed(random.uniform(2,8), download, (connection, self.nomRobot, self.numPaquet) )
    
    def on_privmsg(self, connection, event):
        #DEBUG
        print u"priv --", event.arguments
        msgPriv = self.filtrerCouleur(event.arguments[0])
        secondChannel = self.extraireChannel(msgPriv)
        if ( secondChannel is not None ) :
            if (secondChannel != self.channel):
                self.secondChannel = secondChannel
                print u"connexion au second channel : ", self.secondChannel
                connection.join(self.secondChannel)
        else:
            print u"Pas de channel dans le message prive"
        
    def on_pubmsg(self, cconnection, event):
        pass
        #DEBUG
        #print("pub ---", event.arguments)

    def on_dccmsg(self, connection, event):
        #DEBUG
        #print("dccmsg --", event.arguments)
        
        # Enregistrement dans le fichier des donnees recues
        data = event.arguments[0]
        self.file.write(data)
        self.received_bytes = self.received_bytes + len(data)
        
        # synchro des infos avec le programme principal
        self.objetDL.dejaTelechargeEnMo = (self.position + self.received_bytes)/1048576 # 1024*1024
        self.objetDL.avancement = (self.position + self.received_bytes)/self.objetDL.tailleEnOctets*100
        
        # Ack command ? part of DCC protocol ?
        self.dcc.send_bytes(struct.pack(u"!I", self.received_bytes + self.position))

    def on_dccchat(self, connection, event):
        pass

    def do_command(self, event, cmd):
        pass

    def on_ctcp(self, connection, event):
        #DEBUG
        print u"on_ctcp --", event.arguments
        # Usefull info 
        nick = event.source.nick
        
        # CTCP ANSWER TO : VERSION
        if event.arguments[0] == u"VERSION":
            connection.ctcp_reply(nick, u"VERSION " + self.ctcp_version)
            
        # CTCP ANSWER TO : PING
        elif event.arguments[0] == u"PING":
            if len(event.arguments) > 1:
                connection.ctcp_reply(nick, u"PING " + event.arguments[1])
                
        # CTCP ANSWER TO : SEND => TELECHARGER
        elif len(event.arguments) >= 2:       
            # args = event.arguments[1].split()
            payload = event.arguments[1]
            parts = shlex.split(payload)
            # print u'Parts---', str(parts)
            args = parts
            if args[0] == u"SEND":
                self.filename = downloadPath + os.path.basename(args[1])
                if os.path.exists(self.filename):
                    #DEBUG INFO :
                    print u"A file named", self.filename
                    print u"already exists. Attempting to resume it."
                    
                    # Recupere infos utiles
                    self.objetDL.tailleEnOctets = int(args[4])
                    self.peeraddress = irc.client.ip_numstr_to_quad(args[2])
                    self.position = os.path.getsize(self.filename)
                    
                    # envoi commande resume
                    cmd = u"DCC RESUME #"+ unicode(self.numPaquet) +u" "+ unicode(args[3]) +u" "+ unicode(self.position)
                    connection.ctcp_reply(self.nomRobot, cmd )
                    
                else:
                    # DEBUG INFO :
                    print u"Pas de fichier existant. Debut du DL"    
                    
                    # recuperation de la taille en Octets du fichier
                    self.objetDL.tailleEnOctets = int(args[4])
                    
                    # creation du fichier et connection DCC
                    self.file = open(self.filename, u"wb")
                    peeraddress = irc.client.ip_numstr_to_quad(args[2])
                    peerport = int(args[3])
                    self.dcc = self.dcc_connect(peeraddress, peerport, u"raw")
                    
            elif args[0] == u"ACCEPT" :
                # ouverture du fichier
                print u"on_ctcp RESUME"
                self.file = open(self.filename, u"ab")
                peerport = int(args[2])
                self.dcc = self.dcc_connect(self.peeraddress, peerport, u"raw")
                
            else:
                # Error : (raising exception needed ?)
                print u"bot.py : error : dcc command incomprise"
                self.die()
          
    def on_dcc_disconnect(self, connection, event):
        self.file.close()
        print u"Received file %s (%d bytes)." % (self.filename,
                                                self.received_bytes)
        print u"Maintenant, je vais me coucher, ciao"
        self.objetDL.status = u"fini"
        self.objetDL.avancement = 100
        self.die()

    def on_currenttopic(self, connection, event):
        topic = self.filtrerCouleur(event.arguments[1])
        secondChannel = self.extraireChannel(topic)
        if ( secondChannel is not None ) :
            if (secondChannel != self.channel):
                self.secondChannel = secondChannel
                print u"connexion au second channel : ", self.secondChannel
                connection.join(self.secondChannel)
        else:
            print u"Pas de channel dans le topic"
    
    def filtrerCouleur(self, string):
        return re.sub(
            u'(\\03..\,.)|(\\x03[0-9][0-9])|(\\x03[0-9])|(\\x03)|(\\x1f)|(\\x02)',
            u'',
            string)
    
    def extraireChannel(self, string) :
        channel = re.findall(u'\#\S*',string)
        if (channel == [] ):
            return None
        else :
            return channel[0] 
            
            

################################################################################
# CLASS Download
################################################################################    
class Download(object) :
    def __init__(
            self,
            server = ircDefaultServer,
            channel = ircDefaultChannel,
            nomRobot = ircDefaultNomRobot,
            numPaquet = ircDefaultNumPaquet,
            nickname  =ircDefaultNickname,
            nomFichier = u"Pas de nom defini",
            secondChannel = ircDefaultSecondChannel,
            port = ircDefaultPort
            ):
        if server == u"freenode":
            self.server = u"irc.freenode.net"
        else:
            self.server = u"irc." + server + u".net"
        self.channel = channel
        self.nomRobot = nomRobot
        self.numPaquet = numPaquet
        self.nickname = nickname
        self.secondChannel = secondChannel
        self.nomFichier = nomFichier
        self.port = port
        
        # et pour le partage d'infos :
        self.terminated = False       
        self.dejaTelechargeEnMo = 0
        self.tailleEnOctets = 1048576
        self.status = u"pas commence"
        self.avancement = 0
        
    def startDL(self):
        self.status = u"en cours"
        self.pydccBot = Grabator(
            self,
            self.channel,
            self.nickname, 
            self.server,
            self.numPaquet,
            self.nomRobot,
            self.secondChannel,
            self.port
            )
        self.pydccBot.start()

        
        
            
# TEST DE LA CLASSE GRABATOR, UN XDCC_BOT
if __name__ == u"__main__":
    print u"bot.py - fonction test"
    bot = Grabator()
    bot.start()