from whoosh.index import create_in
# from xbmcswift2 import Plugin
from kodiswift import Plugin
import os
import sys
import re
import json
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import threading
import glob
import shlex
from BeautifulSoup import BeautifulSoup as BS
from whoosh.filedb.filestore import FileStorage
from whoosh.fields import *
from whoosh.qparser import QueryParser
import hurry.filesize as hf
import datetime

# import xbmcswift2_playlists
# import socket

plugin = Plugin()
# lists = xbmcswift2_playlists.Playlists(plugin)
# lib = os.path.join(plugin._addon_id, 'resources', 'lib' )
# print lib

olib = 'special://home' + '/addons/' + plugin._addon_id
lib = xbmc.translatePath(olib)
cache_dir = 'special://home' + '/userdata/addon_data/' \
            + plugin._addon_id
cache_dir += '/cache/'
cache_dir = xbmc.translatePath(cache_dir)
print lib
lib = os.path.join(lib, 'resources', 'lib')
print lib
sys.path.append(lib)

sys.path.append(xbmc.translatePath(os.path.join(os.getcwd(), 'resources'
                                                , 'lib')))

import requests
# from xbmcswift2 import actions
from kodiswift import actions
import cfscrape
from pprint import pformat as pp
# from xdcc import XDCC

import xbot
import dataset
import copy

# from m2g import magnet2torrent as m2t
# from autonomotorrent.BTManager import BTManager
# from autonomotorrent.BTApp import BTApp,BTConfig

# plugin.log.info(cache_dir)
nick = plugin.get_setting('nickname')
db = dataset.connect('sqlite:///' + cache_dir + 'Meta.db')
table = db['meta']
scraper = cfscrape.create_scraper()

# Borrowed from metahandlers

import thetvdbapi

api = thetvdbapi.TheTVDB()

# s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# s.bind((plugin.get_setting('host'),plugin.get_setting('listen_port',int)))

api_key = plugin.get_setting('api_key', str)
api_key = api_key.replace(' ', '')

headers = {'Authorization': api_key}

api_url = 'http://%s:%s/api/1.0/' % (plugin.get_setting('host', str),
                                     plugin.get_setting('port', str))

tmp_path = plugin.get_setting('tmp_path', str)
tmp_path += '*.*'
dl_path = plugin.get_setting('xg_dl_path', str)
dl_path += '*.*'
log = plugin.log.info
whoosh_path = plugin.get_setting('whoosh_path', str)


class SEP(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


FA_api = 'a9494e131f434a23f1c130ec6cb8a2a3'


@plugin.cached_route('/')
def index():
    items = [{'label': 'Search XG...', 'path': plugin.url_for('search',
                                                              search_term='first_page', page='1'),
              'is_playable': False}, {'label': 'Enter Custom Message',
                                      'path': plugin.url_for('play_local_file')},
             {'label': 'Webpage Parsers',
              'path': plugin.url_for('parsers')}]
    # {'label': 'Enter Magnet Link',
    # 'path': plugin.url_for('torrent')}]  # ,

    # {
    # 'label' : 'Enter Custom File Request',
    # 'path' : plugin.url_for('enter_custom')}]

    return items


# @plugin.route('/torrent/')
# def torrent():
# labs = {'title': 'Test'}
# app = BTApp(save_dir=plugin.get_setting('xg_dl_path'),
# listen_port=plugin.get_setting('listen_port', int),
# enable_DHT=True)
# try:
# labs = get_meta()
# except:
# pass
# mag = plugin.keyboard(heading='Enter Magnet Link')
# try:
# Torrent().stop_all_torrents()
# except:
# pass
# app.save_dir = plugin.get_setting('xg_dl_path')
# config = BTConfig(m2t(mag, plugin.get_setting('tmp_path')))
# biggest = 0

# for f in config.metainfo.files:
# if f['length'] > biggest:
# biggest = f['length']
# path = f['path']
# path = plugin.get_setting('xg_dl_path') + path
# plugin.log.info(path)
# app.add_torrent(config)
# manager = BTManager(app, config)
# dialog = xbmcgui.DialogProgress()
# dialog.create('Preparing File')
# threading.Thread(target=manager.app.start_reactor).start()
# while not os.path.exists(path):
# plugin.log.info(manager.get_speed())
# if dialog.iscanceled():
# break
# dialog.close()

# t.join()

# plugin.finish([{
# 'label': labs['title'],
# 'info': labs,
# 'path': path,
# 'context_menu': [('Stop All Torrents',
# actions.background(app.stop_all_torrents()))],
# 'is_playable': True,
# }])


@plugin.route('/search/<search_term>/<page>/')
def search(
        search_term='first_page',
        page='1',
        id=None,
        labs=None,
):
    # packs = xdcc_search.get_packs('http://xdcc.horriblesubs.info','naruto')
    # plugin.log.info('Packs' + str(packs))
    # %s.%s?searchTerm=%s' % (port,type,format,searchTerm)

    if search_term == 'first_page':
        keyboard = xbmc.Keyboard('', 'Enter Search Term', False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_term = keyboard.getText()
    search_packets = 'packets.json?searchTerm=%s&maxResults=20&page=%s' \
                     % (search_term, page)
    request = requests.get(api_url + search_packets, headers=headers)
    results = request.json()

    # results = json.loads(results)

    items = []
    idx = 0
    for option in results['Results']:
        guid_url = api_url + 'packets/%s/enable.json' % option['Guid']
        item = {
            'label': option['Name'] + ' || Size: %s'
                                      % hf.size(option['Size']),
            'path': plugin.url_for('play_file', url=guid_url,
                                   name=option['Name']),
            'is_playable': True,
            'context_menu': [
                ('Assign Metadata', actions.update_view(plugin.url_for(
                    'assign_metadata',
                    id=idx,
                    search_term=search_term,
                    page=page,
                    from_XG=True,
                    name=False,
                    bot=False,
                    cache=False,
                ))),
                ('Reapply Metadata', actions.update_view(plugin.url_for(
                    'assign_metadata',
                    id=idx,
                    search_term=search_term,
                    page=page,
                    from_XG=True,
                    name=False,
                    bot=False,
                    cache=True,
                ))),
                ('Just Download',
                 actions.background(plugin.url_for('just_download',
                                                   url=guid_url, data=False))),
                ('Delete File',
                 actions.background(plugin.url_for('delete_file',
                                                   name=option['Name'], all_files=False))),
                ('Delete All Files',
                 actions.background(plugin.url_for('delete_file',
                                                   name=option['Name'], all_files=True))),
            ],
        }
        try:
            if str(idx) == str(id):
                item['info'] = labs
                item['thumbnail'] = labs['cover_url']
                item['properties'] = \
                    {'Fanart_Image': labs['backdrop_url']}
        except:
            pass
        idx += 1
        items.append(item.copy())

    items.append({'label': 'Next Page >>',
                  'path': plugin.url_for('search',
                                         search_term=search_term, page=str(int(page) + 1))})
    return plugin.finish(items)


# noinspection PyArgumentList
@plugin.route('/play/<name>/<url>/')
def play_file(name, url, data=None):
    if data is None:
        data = {}
    plugin.log.info('Url is: %s' % url)

    # Check to see if file already exists

    tmp_files = glob.glob(tmp_path)
    tmpName = re.sub(r'[\W_]+', '', name)
    tmpName = tmpName.lower()
    dl_file = False
    local_url = ''
    plugin.log.info('Temp Name is' + tmpName)
    dl_files = glob.glob(dl_path)
    for filename in dl_files:
        plugin.log.info('Filepath is ' + re.sub(r'[\W_]+', '',
                                                filename).lower())
        if tmpName in re.sub(r'[\W_]+', '', filename).lower():
            local_url = filename
            dl_file = True
            break
    if local_url == '':
        for filename in tmp_files:
            plugin.log.info('Filepath is ' + filename)
            if tmpName in filename:
                local_url = filename
                break

    if len(local_url) > 0:
        plugin.set_resolved_url(local_url)
    else:

        # if data:
        # headers['Content-Type'] = 'application/json'
        # r = requests.put(url,headers = headers, data = json.dumps(data))
        # plugin.log.info('Url is %s \n Data is %s \n Status is %s \n Text is %s' % (r.url,data,r.status_code,r.text))
        # else: r = requests.post(url,headers=headers)....

        if data:
            stream(
                server=data['server'],
                channel=data['channel'],
                bot=data['bot'],
                packetId=data['packetId'],
                filename=data['packetName'],
                download=True,
            )

        # if manual_meta: infoLabels  = get_meta()
        # else: infoLabels = {'title' : name,'cover_url':''}

        tmp_files = glob.glob(tmp_path)
        tmpName = re.sub(r'[\W_]+', '', name)
        tmpName = tmpName.lower()
        local_url = ''
        plugin.log.info('Temp Name is' + tmpName)
        for filename in tmp_files:
            plugin.log.info('Filepath is ' + filename)
            if tmpName in filename:
                local_url = filename
                break
        plugin.log.info('Playing url: %s' % local_url)

        # item = {'info':infoLabels, 'path' : local_url , 'thumbnail' : infoLabels['cover_url']}

        plugin.set_resolved_url(local_url)


@plugin.route('/play_local_file/')
def play_local_file():
    # tmp_files = glob.glob(tmp_path)
    # keyboard = xbmc.Keyboard('','Enter File Name',False)
    # keyboard.doModal()
    # if keyboard.isConfirmed(): name = keyboard.getText()

    # names = name.strip()
    # local_url = ''
    # for filename in tmp_files:
    # plugin.log.info('Filepath is ' + filename)
    # for term in names:
    # if term in filename:
    # allTerms = True
    # break
    # else:
    # allTerms = False
    # break
    # if allTerms:....local_url = filename
    # if local_url == '':
    # dialog = xbmcgui.Dialog()
    # dialog.notification(message = 'Could Not find file')
    # plugin.log.info('Playing url: %s' % local_url)
    # item = {'path':local_url,'label':name}

    # plugin.set_resolved_url(local_url)

    s = plugin.get_storage('message')
    dialog = xbmcgui.Dialog()
    options = ['Manual', 'Storage']
    storageopt = []

    # try:

    for i in s:
        plugin.log.info(i)
        storageopt.append(i)

    # except: pass

    plugin.log.info(options)
    index = dialog.select('Choose', options)
    if index == 0:
        server = \
            plugin.keyboard(heading='Enter server (Ex: irc.server.net)')
        channel = plugin.keyboard(heading='Enter channel (Ex: #channel)'
                                  )
        s[channel] = {'server': server, 'channel': channel}
    else:
        index = dialog.select('Stored', storageopt)
        server = s[storageopt[index]]['server']
        channel = storageopt[index]
    plugin.log.info(channel + server)
    filename = \
        plugin.keyboard(heading='Enter filename (Ex: A.Movie.mkv)')
    if '#' not in channel:
        channel = '#' + channel
    message = \
        plugin.keyboard(heading='Enter message (Ex: /msg bot xdcc send #packetid)'
                        )
    parts = shlex.split(message)
    bot = parts[1]
    id = parts[4].replace('#', '')
    labs = get_meta()
    return [{
        'label': labs['title'],
        'info': labs,
        'path': plugin.url_for(
            'stream',
            download=False,
            server=server,
            channel=channel,
            bot=bot,
            packetId=id,
            filename=filename,
        ),
        'is_playable': True,
    }]


@plugin.route('/webpages/')
def parsers():
    items = [{'label': 'Add a Channel...',
              'path': plugin.url_for('add_server')},
             {'label': 'Search ixIRC...',
              'path': plugin.url_for('search_ix', query='**just_search**'
                                     , page='0')}, {'label': 'Search Haruhichan...',
                                                    'path': plugin.url_for('haruhichan', key='None')},
             {'label': 'Search xweasel...', 'path': plugin.url_for('xweasel', query='lala', page='1')},
             {'label': 'Ginpachi-Sensei', 'path': plugin.url_for('gin_sensei', search='blah')},
             {'label': 'Hi10', 'path': plugin.url_for('cloud10')}]
    for storage in plugin.list_storage():
        if storage == 'meta_cache' or storage == 'showcache' or storage \
                == 'message':
            continue
        try:
            storage = plugin.get_storage(storage)
        except:
            continue
        # plugin.log.info('Storage %s' % storage)
        try:
            items.append({'label': storage['name'],
                          'path': plugin.url_for('channel',
                                                 name=storage['name']),
                          'context_menu': [('Refresh Packlist',
                                            actions.background(plugin.url_for('refresh',
                                                                              name=storage['name']))), ('Refresh Local Packlist',
                                            actions.background(plugin.url_for('refresh',
                                                                              name=storage['name']+".Local"))),('Refresh AniDB',
                                                                                                        actions.background(
                                                                                                            plugin.url_for(
                                                                                                                'refresh',
                                                                                                                name='animetitles')))]})
        except:
            pass
    return items


@plugin.route('/add_server/')
def add_server():
    global name, server, url
    keyboard = xbmc.Keyboard('',
                             'Enter Host Server (Ex: irc.server.net)',
                             False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        server = keyboard.getText()
    keyboard = xbmc.Keyboard('', 'Enter Channel Name', False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        name = keyboard.getText()
    channel = plugin.get_storage('%s' % name, ttl=60 * 24 * 5)
    channel['name'] = name
    keyboard = xbmc.Keyboard('',
                             'Enter Webpage Url (Ex: http://xdcc.channel.com/'
                             , False)
    keyboard.doModal()
    if keyboard.isConfirmed():
        url = keyboard.getText()
    packlist = get_packlist(url)
    channel['url'] = url
    channel['server'] = server
    channel['packlist'] = packlist
    channel['bots'] = []


@plugin.cached_route('/webpages/<name>/')
def channel(name):
    items = [{'label': 'Search Packlist...',
              'path': plugin.url_for('search_channel', name=name,
                                     bot='list_all')}, {'label': 'List All Packlist',
                                                        'path': plugin.url_for('list_packlist', name=name,
                                                                               search_term='list_all', bot='list_all',
                                                                               page='1')},
             {'label': 'List Bots', 'path': plugin.url_for('list_bots',
                                                           channel=name)}]
    return items


def file_meta(name):
    wstorage = FileStorage(whoosh_path)
    ix = wstorage.open_index()
    google = ix.searcher()
    try:
        show, ep = name.split(']')[1].split('[')[0].lstrip().rstrip().replace(' - ', ' ').rpartition(
            re.search('\d{1,3}', name).group(0))[:2]
    except:
        show = name.split('_-_')[0].rpartition(')_')[2].replace('_', ' ')
        ep = name.split('_-_')[1].split('_')[0]
    plugin.log.info('ShowEp %s %s' % (show, ep))
    if int(ep) == 0: return {}
    info = plugin.get_storage('%s' % show)
    infoLabels = {}
    plugin.log.info('SHOW STORAGE %s' % pp([x for x in info.items() if len(repr(x[1])) < 20]))
    if len(info.keys()) == 0 or info is None or (
                    'last' in info.keys() and datetime.datetime.today().toordinal() - info['last'] >= 5):
        info['last'] = datetime.datetime.today().toordinal()
        query = QueryParser("title", ix.schema).parse(show)
        results = google.search(query)
        plugin.log.info('SEARCH %s' % pp([(x['title'], x['content']) for x in results[:5]]))
        info['noresults'] = 0 if len(results) else 1
        v = []
        ot = None
        if len(results):
            aid = results[0]['aid']
            info['aid'] = aid
            log('REQUESTING ANIDB DATA')
            r = requests.get(
                'http://api.anidb.net:9001/httpapi?request=anime&client=anidbtvdbmeta&clientver=1&protover=1&aid=%s' % aid)
            log("Status %s\n" % r.status_code)
            soup = BS(r.text)
            v = [x for x in soup.findAll('epno') if x.text == str(int(ep))]
            info['aniupdate'] = 0 if len(v) else 1
            plugin.log.info('V %s' % v)
            '''try:
                log('CHANGING SHOW SEARCH FROM %s to %s' %(show,results[0]['content'][0]))
                show = results[0]['content'][0]
            except:
                pass'''
            ot = results[0]['content']
            ot = [ot[-1]] + ot[:-1]
            log('OT %s' % ot)
        google.close()
        id = None
        theaders = {'Content-Type': 'application/json',
                    'trakt-api-version': '2',
                    'trakt-api-key': '05bcd2c0baf2685b8c196162d099e539033c21f7aa9fe1f87b234c2d62c2c1e4'}
        results = \
            requests.get('https://api-v2launch.trakt.tv/search?query=%s&type=show'
                         % show, headers=theaders)
        log('STATUS %s' % results)
        results = results.json()
        # results = api.get_matching_shows(title)
        search_meta = []
        for item in results:
            option = {
                'tvdb_id': item['show']['ids']['tvdb'],
                'title': item['show']['title'],
                'imdb_id': item['show']['ids']['imdb'],
                'trakt_id': item['show']['ids']['trakt'],
            }
            search_meta.append(option)
        log('Search Meta %s' % pp(search_meta))
        if len(search_meta):
            id = str(search_meta[0]['tvdb_id'])
            info['id'] = id
            log('ID %s' % id)
        else:
            shws = api.get_matching_shows(show)
            log('Matching Shows %s' % pp(shws))
            try:
                id = shws[0][0] if show != 'Drifters' else shws[1][0]
            except:
                if ot is not None:
                    for x in ot:
                        try:
                            id = api.get_matching_shows(x)[0][0] if show != 'Drifters' else \
                                api.get_matching_shows(x)[1][0]
                            if len(id) > 0: break
                        except:
                            pass
        info['noid'] = 0 if id is not None else 1
        if id is None: return {}
        info['id'] = id
        if info['noid'] == 0: info['aniupdate'] = 0
        e = api.get_show_and_episodes(id)
        info['shownep'] = [e[0].__dict__, [i.__dict__ for i in e[1]]]
        log(pp(info))
        if len(v):
            info['anidb'] = repr(v[0].parent.parent)

            try:
                info['EP%sairdate' % ep] = v[0].parent.airdate.text
                log('AIRDATE %s' % v[0].parent.airdate.text)
                airdate = api.convert_date(v[0].parent.airdate.text)
                episode = [i for i in e[1] if 2 >= (lambda x: x.days)(
                    airdate - api.convert_date(
                        i.first_aired) if i.first_aired else airdate - airdate) >= -2]  # Was a -9 after else

            except Exception, ed:
                #log(e.__dict__)
                log('ERROR %s LINE: %s' % (ed, sys.exc_info()[2].tb_lineno))
                log('AIRDATE DIDNT WORK ON EPISODE %s' % ep)
                try:
                    episode = [i for i in e[1] if int(i.absolute_number) == int(ep)]
                except:
                    episode = [i for i in e[1] if int(i.episode_number) == int(ep)]
            info['tvupdate'] = 0 if len(episode) else 1
            try:
                infoLabels = transform_ep_object(episode[0])
            except Exception, excptn:
                log('ERROR %s LINE: %s' % (excptn, sys.exc_info()[2].tb_lineno))
            infoLabels['TVShowTitle'] = e[0].name
            infoLabels['backdrop_url'] = e[0].fanart_url
            info['EP%s' % ep] = infoLabels
            plugin.log.info('INFO %s' % info.keys())
            return infoLabels
        elif id:
            episode = [x for x in e[1] if
                       (lambda i: int(i.absolute_number) if i.absolute_number != '' else int(i.episode_number))(
                           x) == int(ep)]
            info['tvupdate'] = 0 if len(episode) else 1
            try:
                infoLabels = transform_ep_object(episode[0])
            except Exception, excptn:
                log('ERROR %s LINE: %s' % (excptn, sys.exc_info()[2].tb_lineno))
            infoLabels['TVShowTitle'] = e[0].name
            infoLabels['backdrop_url'] = e[0].fanart_url
            info['EP%s' % ep] = infoLabels
            plugin.log.info('INFO %s' % info.keys())
            return infoLabels
    else:
        if 'EP%s' % ep in info.keys():
            infoLabels = info['EP%s' % ep]
            return infoLabels
        if info['noid']: return {}
        if info['aniupdate']:
            query = QueryParser("title", ix.schema).parse(show)
            results = google.search(query)
            aid = results[0]['aid']
            google.close()
            info['aid'] = aid
            r = requests.get(
                'http://api.anidb.net:9001/httpapi?request=anime&client=anidbtvdbmeta&clientver=1&protover=1&aid=%s' % aid)
            log("Status %s\n" % r.status_code)
            log("HTML CODE: %s" % r.text)
            soup = BS(r.text)
            v = [x for x in soup.findAll('epno') if x.text == str(int(ep))]
            info['anidb'] = repr(v[0].parent.parent)
            info['EP%sairdate' % ep] = v[0].parent.airdate.text
            info['aniupdate'] = 0 if len(v) else 1

        if info['tvupdate']:
            e = api.get_show_and_episodes(info['id'])
            info['shownep'] = [e[0].__dict__, [i.__dict__ for i in e[1]]]
            try:
                airdate = api.convert_date(info['EP%sairdate' % ep])
                episode = [i for i in e[1] if 2 >= (lambda x: x.days)(airdate - api.convert_date(i.first_aired)) >= -2]
            except Exception, excptn:
                log('ERROR %s LINE: %s' % (excptn, sys.exc_info()[2].tb_lineno))
                try:
                    episode = [i for i in e[1] if int(i.absolute_number) == int(ep)]
                except:
                    episode = [i for i in e[1] if int(i.episode_number) == int(ep)]
            info['tvupdate'] = 0 if len(episode) else 1
            try:
                infoLabels = transform_ep_object(episode[0])
            except Exception, excptn:
                log('ERROR %s LINE: %s' % (excptn, sys.exc_info()[2].tb_lineno))
            infoLabels['TVShowTitle'] = e[0].name
            infoLabels['backdrop_url'] = e[0].fanart_url
            info['EP%s' % ep] = infoLabels
            return infoLabels
        if 'EP%s' % ep not in info.keys():
            e = [SEP(**info['shownep'][0]), [SEP(**i) for i in info['shownep'][1]]]
            try:
                soup = BS(info['anidb'])
                v = [x for x in soup.findAll('epno') if x.text == str(int(ep))]
                info['EP%sairdate' % ep] = v[0].parent.airdate.text
                airdate = api.convert_date(v[0].parent.airdate.text)
                episode = [i for i in e[1] if 2 >= (lambda x: x.days)(airdate - api.convert_date(i.first_aired)) >= -2]
                info['tvupdate'] = 0 if len(episode) else 1
                try:
                    infoLabels = transform_ep_object(episode[0])
                except Exception, excptn:
                    log(excptn)
                infoLabels['TVShowTitle'] = e[0].name
                infoLabels['backdrop_url'] = e[0].fanart_url
                info['EP%s' % ep] = infoLabels
                plugin.log.info('INFO %s' % info.keys())
                return infoLabels
            except Exception, er:
                plugin.log.info('EP ERROR %s' % er)
            try:
                episode = [x for x in e[1] if x.absolute_number != '' and int(x.absolute_number) == int(ep)]
            except:
                episode = [x for x in e[1] if x.episode_number != '' and int(x.episode_number) == int(ep)]
            info['tvupdate'] = 0 if len(episode) else 1
            infoLabels = transform_ep_object(episode[0])
            infoLabels['TVShowTitle'] = e[0].name
            infoLabels['backdrop_url'] = e[0].fanart_url
            info['EP%s' % ep] = infoLabels
            plugin.log.info('INFO %s' % info.keys())
            return infoLabels
        else:
            return {}


@plugin.route('/webpages/<name>/list_packlist/<bot>/<search_term>/<page>')
def list_packlist(
        name,
        search_term='',
        bot='',
        page='1',
        labs=None,
        id='',
        cache='nope'
):
    global all_Terms
    if labs is None:
        labs = {}
    page = int(page)
    cache = plugin.get_storage('%s' % name)
    log(cache.keys())
    packlist = copy.copy(cache['packlist'])
    items = []
    prev = (page - 1) * 20
    curr = page * 20
    if bot != 'list_all':
        bot_packlist = []
        for item in packlist:
            if bot == item['bot']:
                bot_packlist.append(item)
        packlist = bot_packlist

    if search_term != 'list_all':
        search_packlist = []
        search_terms = search_term.split()
        plugin.log.info('Search Terms %s' % search_terms)
        for i in packlist:
            for term in search_terms:
                if term.lower() in i['filename'].lower():
                    all_Terms = True
                else:
                    all_Terms = False
                    break
            if all_Terms:
                search_packlist.append(i)
        packlist = search_packlist
    idx = 0
    for item in packlist:  # [prev:curr]:
        flabs = {'title':'','plot':'','season':'','episode':'','premiered':''}
        try:
            flabs.update(file_meta(item['filename']))
            flabs['plot'] = item['filename'] + ' || Size: ' + str(item['size']) + ' MB || Bot : ' + item[
                'bot'] + '\n\n' + flabs['plot']
            log(flabs['premiered'])
            try:
                flabs['Size'] = api.convert_date(flabs['premiered']).toordinal()
            except Exception, e:
                log(e)
                flabs['Size'] = flabs['premiered']
        except Exception, ed:
            log('ERROR %s LINE: %s' % (ed, sys.exc_info()[2].tb_lineno))
            flabs = {}

        log(pp(flabs))
        items.append({
            'label': item['filename'] + ' || Size: '
                     + str(item['size']) + ' MB || Bot : ' + item['bot'
                     ],
            'path': plugin.url_for(
                'stream',
                download=item['size'],
                server=cache['server'],
                channel=name,
                bot=item['bot'],
                packetId=item['packetId'],
                filename=item['filename'],
            ),
            'is_playable': True,
            'context_menu': [('Assign Metadata',
                              actions.update_view(plugin.url_for(
                                  'assign_metadata',
                                  id=idx,
                                  search_term=search_term,
                                  page=page,
                                  name=name,
                                  bot=bot,
                                  from_XG=False,
                                  cache=False,
                              ))), ('Reapply Metadata',
                                    actions.update_view(plugin.url_for(
                                        'assign_metadata',
                                        id=idx,
                                        search_term=search_term,
                                        page=page,
                                        name=name,
                                        bot=bot,
                                        from_XG=False,
                                        cache='reapply',
                                    ))), ('Next Episode',
                                          actions.update_view(plugin.url_for(
                                              'assign_metadata',
                                              id=idx,
                                              search_term=search_term,
                                              page=page,
                                              name=name,
                                              bot=bot,
                                              from_XG=False,
                                              cache='next',
                                          ))), ('Previous Episode',
                                                actions.update_view(plugin.url_for(
                                                    'assign_metadata',
                                                    id=idx,
                                                    search_term=search_term,
                                                    page=page,
                                                    name=name,
                                                    bot=bot,
                                                    from_XG=False,
                                                    cache='prev',
                                                ))), ('File Metadata',
                                                      actions.update_view(plugin.url_for(
                                                          'assign_metadata',
                                                          id=idx,
                                                          search_term=search_term,
                                                          page=page,
                                                          name=name,
                                                          bot=bot,
                                                          from_XG=False,
                                                          cache=item['filename']
                                                      ))), ('Just Download',
                                                            actions.background(plugin.url_for(
                                                                'stream',
                                                                download=True,
                                                                server=cache['server'],
                                                                channel=name,
                                                                bot=item['bot'],
                                                                packetId=item['packetId'],
                                                                filename=item['filename'],
                                                            ))), ('Delete File',
                                                                  actions.background(plugin.url_for('delete_file'
                                                                                                    , name=item[
                                                                          'filename'],
                                                                                                    all_files=False))),
                             ('Delete All Files',
                              actions.background(plugin.url_for('delete_file'
                                                                , name=item['filename'], all_files=True)))],
            'info': flabs if flabs else '',
            'thumbnail': flabs['cover_url'] if 'cover_url' in flabs.keys() else '',
            'properties': {'Fanart_Image': flabs['backdrop_url']} if 'backdrop_url' in flabs.keys() else '',
            'info_type': 'video'
        })
        try:
            if str(idx) == str(id):
                items[idx]['info'] = labs
                items[idx]['thumbnail'] = labs['cover_url']
                items[idx]['properties'] = \
                    {'Fanart_Image': labs['backdrop_url']}
        except:
            pass
        idx += 1
    # if curr <= len(packlist):
    # items.append({'label': 'Next Page >>',
    # 'path': plugin.url_for('list_packlist', name=name,
    # search_term=search_term, bot=bot, page=str(page
    # + 1))})
    # if page > 1:
    # items.insert(0, {'label': '<< Previous Page',
    # 'path': plugin.url_for('list_packlist', name=name,
    # search_term=search_term, bot=bot, page=str(page
    # - 1))})
    plugin.finish(items=items, sort_methods=['Size'])


@plugin.route('/webpages/<name>/search/<bot>/')
def search_channel(name, bot='all_bots'):
    lastsearch = plugin.get_storage('lastsearch')
    if 'last' not in lastsearch.keys():
        lastsearch['last'] = ''
    search_term = plugin.keyboard(default=lastsearch['last'], heading='Enter Search Term')
    lastsearch['last'] = search_term
    return list_packlist(name=name, search_term=search_term, page='1', bot=bot)


# plugin.finish(items=[{'label': 'Results',
# 'path': plugin.url_for('list_packlist', name=name, search_term=search_term, page='1',
# bot=bot)}])


@plugin.route('/webpages/<channel>/bots/')
def list_bots(channel):
    cache = plugin.get_storage(channel)
    packlist = cache['packlist']
    log(cache.keys())
    if not cache['bots']:
        for item in packlist:
            log('KEYS %s' % item.keys())
            if item['bot'] not in str(cache['bots']):
                cache['bots'].append({'label': item['bot'],
                                      'path': plugin.url_for('bots', channel=channel,
                                                             bot=item['bot'])})

    return cache['bots']


@plugin.cached_route('/webpages/<channel>/bots/<bot>/')
def bots(channel, bot):
    return [{'label': 'Search Bot Packlist',
             'path': plugin.url_for('search_channel', name=channel,
                                    bot=bot)}, {'label': 'List All Packs for %s' % bot,
                                                'path': plugin.url_for('list_packlist', name=channel,
                                                                       search_term='list_all', bot=bot, page='1')}]


@plugin.route('/update_packlist/<name>/')
def refresh(name):
    if name == 'animetitles':
        # t = requests.get('http://anidb.net/api/anime-titles.xml.gz')
        # log('ANITITLES STATUS %s' % t.status_code)
        anilist = xbmc.translatePath(olib) + '\\anime-titles.xml'
        import shutil
        with open(anilist, 'rb') as ani:
            soup = BS(ani)
        log('FINISHED PARSING BS ANITITLES')
        shutil.rmtree(whoosh_path)
        os.mkdir(whoosh_path)
        log('REMOVED ORIGINAL WHOOSH PATH')
        wstorage = FileStorage(whoosh_path)
        # ix = wstorage.open_index()
        log('OPENING WHOOSH INDEX')
        schema = Schema(title=TEXT(stored=True), aid=NUMERIC(stored=True), content=NGRAMWORDS(stored=True))
        ix = create_in(whoosh_path, schema)
        writer = ix.writer()
        log('BEGINNING WRITING PROCESS')
        for x in soup.findAll('title', type='main'):
            c = [unicode(i.text) for i in x.parent.findAll('title', attrs={'xml:lang': 'en'})]
            c.append(unicode(x.text))
            writer.add_document(title=x.text, aid=x.parent['aid'], content=c)
        writer.commit()
        log('FINISHED WRITING PROCESS')
    local = 0
    if '.Local' in name:
        local = 1
        name=name.split('.Local')[0]
    storage = plugin.get_storage(name)
    if local:
        if 'local' not in storage.keys():
            storage['local'] = plugin.keyboard(heading='Enter local Packlist location')
        if 'packlist' not in storage.keys():
            storage['packlist'] = ''
        storage['packlist'] = get_packlist(storage['local'],local)
    else:
        storage['packlist'] = get_packlist(storage['url'],local)
    y = len(storage['packlist'])
    dlg = xbmcgui.DialogProgress()
    x = 0
    dlg.create("Refreshing...")
    for item in storage['packlist']:
        if item['bot'] not in str(storage['bots']):
            storage['bots'].append({'label': item['bot'],
                                    'path': plugin.url_for('bots',
                                                           channel=name, bot=item['bot'])})
            x += 1
            dlg.update(int(float((x / y)) * 100), item['bot'])


def get_packlist(url,local=0):

    if local==0:
        url += 'search.php'
        specific = xbmcgui.Dialog().yesno('Select Specific Bot',"Add a Specific Bot Nickname?")
        if specific:
            url+= '?nick=' + plugin.keyboard()
        try:
            r = scraper.get(url)
        except:
            r = requests.get(url)
        plugin.log.info('Packlist Status %s' % r)
        if str(r.status_code) != '200':
            xbmcgui.Dialog().ok(line1 = "Failed to get Packlist status %s" % r.status_code, heading = '')
        text = r.text
    else:
        text = open(url, 'rb').read()
    m = re.findall('= (.+?);\n', text)
    items = []
    for item in m:
        item = item.replace('b:', "'bot':").replace('n:', "'packetId':"
                                                    ).replace('f:', "'filename':").replace('s:', "'size':")
        try:
            dict = eval(item)
            items.append(dict.copy())
        except:
            pass
    return items


@plugin.cached(ttl=60 * 24 * 3)
def get_gin():
    plugin.log.info('Getting Text')
    with open(cache_dir + 'Gin.txt', 'wb') as gtxt:
        gtxt.write(scraper.get('https://gin.sadaharu.eu/Gin.txt').text)
    with open(cache_dir + 'Gin.txt', 'rb') as gtxt:
        items = []
        for x in gtxt.readlines():
            if x[0] == '#' and x[:3] != '#1 ':
                num = x.find(' ')
                num = x[1:num]
                s = x.find('[') + 1
                f = x.find(']') - 1
                size = x[s:f]
                size = int(size) if '.' not in size else float(size)
                if size < 100 and x[f] == 'M': size *= 10
                if x[f] == 'G': size = int(hf.size(size * 1073741824, [(1048576, '')]))
                if x[f] == 'K': size = int(hf.size(size * 1024, [(1048576, '')]))
                name = x[f + 3:-1]
                items.append({'packetId': num, 'filename': name, 'bot': 'Gintoki', 'size': size})
    g = plugin.get_storage('Ginpachi-Sensei')
    g.update({'packlist': items, 'server': 'irc.rizon.net'})


@plugin.route('/gin_sensei/<search>')
def gin_sensei(search):
    get_gin()
    if search != 'none':
        lastsearch = plugin.get_storage('lastsearch')
        search = plugin.keyboard(default=lastsearch['last'], heading='Enter Search Term')
        lastsearch['last'] = search
    return [{'label': 'Results',
             'path': plugin.url_for(list_packlist, name='Ginpachi-Sensei', search_term=search, page='1',
                                    bot='Gintoki')}]


@plugin.route('/stream/<download>/<server>/<channel>/<bot>/<packetId>/<filename>')
def stream(
        server,
        channel,
        bot,
        packetId,
        filename,
        download=False,
):
    if '#' not in channel:
        channel = '#' + channel
    data = {
        'server': server,
        'channel': channel,
        'bot': bot,
        'packetId': int(packetId),
        'packetName': filename,
    }

    # dl_path = plugin.get_setting('xg_dl_path',str)
    # plugin.log.info(dl_path)
    # from data import Networks
    # networks = Networks()
    # import socket
    # server =....socket.gethostbyname(server)
    fstring = plugin.get_setting('xg_dl_path', str) + filename.replace("'","_")
    log(fstring)
    log('EXISTS %s' % os.path.exists(fstring))
    if bot == 'Ginpachi-Sensei': bot = 'Gintoki'
    plugin.log.info(channel)
    # if str(download) == 'True':
    # pass
    # else:
    # return play_file(filename, url='', data=data)
    if download == 'True' or not os.path.exists(fstring):
        log('IRC DOWNLOAD')
        sc = '#mg-chat' if channel == '#moviegods' else None
        sc = '#zw-chat' if channel == '#Zombie-Warez' else None

        c = xbot.Download(channel=channel, server=server,
                          numPaquet=int(packetId), nomRobot=bot, secondChannel=channel,
                          nickname=nick)
        if channel == '#moviegods':
            c.secondChannel = '#mg-chat'
        if channel == '#Zombie-Warez':
            c.secondChannel = '#zw-chat'
        if channel == '#Ginpachi-Sensei':
            c.secondChannel = ''
        d = xbot.Grabator(
            channel=channel,
            secondChannel='',
            server=server,
            numPaquet=int(packetId),
            nomRobot=bot,
            nickname=nick,
            objetDL=c
        )
        if channel == '#moviegods':
            d.secondChannel = '#mg-chat'
        if channel == '#Ginpachi-Sensei':
            d.secondChannel = ''
        t = threading.Thread(target=d.start)
        t.start()
    # x.start()
    # t = threading.Thread(target=d.start)
    # t.start()
    # t.join()

    streamlink = 'http://localhost:9085/vfs/%s' % fstring
    if download.isdigit():
        log('Start play process')
        dialog = xbmcgui.DialogProgress()
        size = float(download)
        status = lambda x: (float(x) / size) * 100

        dialog.create('Downloading File', 'Checking if it Exists...')
        cancel = 0
        tsys = copy.copy(hf.traditional)
        tsys = [(tsys[-3][0], '')]
        b = plugin.get_setting('bf_time', int)
        up = dialog.update
        log('Checking existence')
        while not os.path.exists(fstring):
            up(0)
            if dialog.iscanceled():
                cancel = 1
                break
        log('Found')
        up(0, 'File Found')
        xsize = os.path.getsize(fstring)
        import timeit
        start = timeit.default_timer()
        wait = 0
        ysize = 0
        from VideoParser import VideoParser as VP

        while wait <= 5:
            up(int(status(hf.size(os.path.getsize(fstring), tsys))),
               'Downloading File', '{} of {}'.format(hf.size(os.path.getsize(fstring),
                                                             hf.traditional),
                                                     size))
            ysize = os.path.getsize(fstring) - xsize
            wait = timeit.default_timer() - start
        spd = (ysize / wait) / float(hf.alternative[3][0])
        log('SPEED %.2f M/s' % spd)
        # lngth = 0
        # from multiprocessing.pool import ThreadPool
        # p = ThreadPool(1)
        # l = p.apply_async(VP().getVideoLength,(fstring,))

        # while lngth == 0:
        # lngth = l.get()
        # log('VP Length %s' % lngth)
        factor = b * (((size / 1420) * 2) / spd) if ysize != 0 else b
        log('FACTOR %s' % factor)
        factor = factor if factor <= 100 else 90
        while status(hf.size(os.path.getsize(fstring),
                             tsys)) <= factor:  # ((float(size)/5)/size)*.6*100:# while status(hf.size(os.path.getsize(fstring), tsys)) <= b:
            up(int(status(hf.size(os.path.getsize(fstring), tsys))),
               'Downloading File', '{} of {}'.format(hf.size(os.path.getsize(fstring),
                                                             hf.traditional),
                                                     size))
            if dialog.iscanceled():
                cancel = 1
                break
        log('Cancel: %s' % cancel)
        if not cancel:
            dialog.close()
            plugin.set_resolved_url(fstring)


def get_meta():
    dialog = xbmcgui.Dialog()
    showcache = plugin.get_storage('showcache')

    optionlist = ['tvshow', 'movie', 'Storage', 'none']
    storagelist = []
    try:
        for show in showcache:
            plugin.log.info(showcache)
            storagelist = [x for x in showcache if x != 'last']
        plugin.log.info(storagelist)
    except Exception, e:
        plugin.log.info('ERROR %s' % e)
    imdb = ''
    tvdb = ''
    tmdb = ''
    headers = {'Content-Type': 'application/json',
               'trakt-api-version': '2',
               'trakt-api-key': '05bcd2c0baf2685b8c196162d099e539033c21f7aa9fe1f87b234c2d62c2c1e4'}
    index = dialog.select('Choose Video Type', optionlist)
    stype = optionlist[index]
    search_meta = []
    option_list = []
    if index == 3: return {}
    plugin.log.info('INDEX: %s' % index)
    if index == 0 or index == 2:
        if stype == 'tvshow':
            keyboard = xbmc.Keyboard('', 'Enter a Title', False)
            keyboard.doModal()
            if keyboard.isConfirmed():
                title = keyboard.getText()
            results = \
                requests.get('https://api-v2launch.trakt.tv/search?query=%s&type=show'
                             % title, headers=headers).json()

            # results = api.get_matching_shows(title)

            for item in results:
                option = {
                    'tvdb_id': item['show']['ids']['tvdb'],
                    'title': item['show']['title'],
                    'imdb_id': item['show']['ids']['imdb'],
                    'trakt_id': item['show']['ids']['trakt'],
                    'year': item['show']['year']
                }
                search_meta.append(option)
            for option in search_meta:
                disptitle = option['title'] + ' (' + str(option['year']) + ')'
                option_list.append(disptitle)
            index = dialog.select('Choose', option_list)
            Show = search_meta[index]
            shownep = api.get_show_and_episodes(Show['tvdb_id'])

            showcache[str(Show['title'])] = {'title': Show['title'],
                                             'data': [shownep[0].__dict__, [x.__dict__ for x in
                                                                            shownep[1]]],
                                             'day': datetime.datetime.today().toordinal()}
            showcache['last'] = showcache[str(Show['title'])]
        elif stype == 'Storage':

            # xbmc.sleep(200)
            # showcache.sync()
            today = datetime.datetime.today().toordinal()
            index = dialog.select('Stored Meta', storagelist)

            sdata = showcache[storagelist[index]]
            showcache['last'] = sdata

            data = sdata['data']
            if today - sdata['day'] <= 5:
                shownep = [SEP(**data[0]), [SEP(**x) for x in data[1]]]
            else:
                shownep = api.get_show_and_episodes(data[0]['id'])
                showcache[storagelist[index]]['data'] = [shownep[0].__dict__, [x.__dict__ for x in shownep[1]]]
            plugin.log.info('STORAGE FOUND')
            stype = 'tvshow'
            Show = {'title': shownep[0].name, 'tvdb_id': shownep[0].id,
                    'imdb_id': shownep[0].imdb_id}
        option2 = '-1'
        season_list = []
        for item in shownep[1]:
            if option2 != item.season_number:
                option2 = item.season_number
                ep_list = []
                for item2 in shownep[1]:
                    if item2.season_number == option2:
                        ep_list.append(item2)
                start_ep = ep_list[0].absolute_number
                end_ep = ep_list[-1].absolute_number
                season_list.append('Season %s Episodes (%s - %s)'
                                   % (option2, start_ep, end_ep))
        index = dialog.select('Choose Season', season_list)
        season = re.search('Season (.+?) Episodes',
                           season_list[index]).group(1)
        episode_list = [[], []]
        plugin.log.info('SEASON' + season)
        for item in shownep[1]:
            if item.season_number == season:
                disptitle = '%sx%s (%s) %s' % (item.season_number,
                                               item.episode_number, item.absolute_number,
                                               item.name)
                episode_list[0].append(disptitle)
                episode_list[1].append(item)
        index = dialog.select('Choose Episode', episode_list[0])

        episode = episode_list[1][index]
        showcache['last']['index'] = showcache['last']['data'][1].index(episode.__dict__)
        # keyboard = xbmc.Keyboard('','Enter a Season',False)
        # keyboard.doModal()
        # if keyboard.isConfirmed(): season = keyboard.getText()
        # keyboard = xbmc.Keyboard('','Enter an Episode',False)
        # keyboard.doModal()
        # if keyboard.isConfirmed(): episode = keyboard.getText()
        # episode = shownep[1][episode]api.get_episode_by_season_ep(Show['tvdb_id'],season,episode)

        try:
            infoLabels = transform_ep_object(episode)
        except Exception, e:
            log(e)
        infoLabels['TVShowTitle'] = Show['title']
        imdb = Show['imdb_id']
        tvdb = Show['tvdb_id']
        img = infoLabels['cover_url']
        infoLabels['backdrop_url'] = shownep[0].fanart_url

        plugin.log.info('INFO Labels \t %s' % infoLabels)
    elif stype == 'movie':

        title = plugin.keyboard(heading='Enter a Title')
        results = \
            requests.get('https://api-v2launch.trakt.tv/search?query=%s&type=movie'
                         % title, headers=headers).json()
        plugin.log.info('Results %s' % results)

        for option in results:
            disptitle = '%s (%s)' % (option['movie']['title'],
                                     option['movie']['year'])
            option_list.append(disptitle)
        dialog = xbmcgui.Dialog()
        index = dialog.select('Choose', option_list)
        Movie = results[index]['movie']

        plugin.log.info('Movie: %s' % Movie)
        infoLabels = {'cover_url': Movie['images']['poster']['medium'], 'plot': Movie['overview'],
                      'backdrop_url': Movie['images']['fanart']['full'], 'year': Movie['year'], 'title': Movie['title']}

    # if stype == 'tvshow':
    # api_url = 'https://api-v2launch.trakt.tv/search?id_type=trakt-show&id=%s' % (Show['trakt_id'])
    # request = requests.get(api_url, headers=headers)
    # plugin.log.info('TRAKT JSON %s' % request.json())
    # trakt_meta = request.json()[0]['show']

    # plugin.log.info("Trakt_meta %s" % trakt_meta)

    # infoLabels['TVShowTitle'] = trakt_meta['title']
    # infoLabels['backdrop_url'] = trakt_meta['images']['fanart']['full']

    plugin.log.info('infoLabels: %s' % infoLabels)
    latest = infoLabels
    latest['latest'] = 'latest'
    table.delete(latest='latest')
    table.upsert(latest, ['latest'])
    return infoLabels


def transform_ep_object(episode):
    meta = {'episode_id': episode.id, 'plot': api.check(episode.overview)}
    if episode.guest_stars:
        guest_stars = episode.guest_stars
        if guest_stars.startswith('|'):
            guest_stars = guest_stars[1:-1]
        guest_stars = guest_stars.replace('|', ', ')
        meta['plot'] = meta['plot'] + 'Guest Starring: ' \
                       + guest_stars
    meta['rating'] = float(api.check(episode.rating, 0))
    meta['premiered'] = api.check(episode.first_aired)
    meta['title'] = api.check(episode.name)
    meta['poster'] = api.check(episode.image)
    meta['director'] = api.check(episode.director)
    meta['writer'] = api.check(episode.writer)
    meta['season'] = int(api.check(episode.season_number, 0))
    meta['episode'] = int(api.check(episode.episode_number, 0))
    meta['cover_url'] = api.check(episode.image)
    return meta


@plugin.route('/delete_file/<name>/<all_files>')
def delete_file(name, all_files=False):
    plugin.log.info('NAME ' + name)
    tmp_files = glob.glob(tmp_path)
    dl_files = glob.glob(dl_path)
    import shutil
    if str(all_files) == 'True':
        try:
            for file in dl_files:
                log('Deleting %s ...' % file)
                try:
                    shutil.rmtree(file)
                except Exception, e:
                    os.remove(file)
                    log('DELETE ALL FILES ERROR: %s' % e)
                    continue
        except Exception, e:
            log('DELETE ALL FILES ERROR: %s' % e)
            pass
        try:
            for file in tmp_files:
                shutil.rmtree(file)
        except:
            pass
    tmpName = re.sub(r'[\W_]+', '', name)
    tmpName = tmpName.lower()
    plugin.log.info('Temp Name is' + tmpName)
    try:
        for filename in tmp_files:
            plugin.log.info('Filepath is ' + filename)
            if tmpName in filename.lower():
                os.remove(filename)
    except:
        pass
    try:
        for filename in dl_files:
            if tmpName in re.sub(r'[\W_]+', '', filename.lower()):
                os.remove(filename)
    except:
        pass


@plugin.route('/webpages/search_ix/<query>/<page>')
def search_ix(
        query='**just_search**',
        page='0',
        id=-1,
        labs=None,
):
    if labs is None:
        labs = {}
    page = int(page)
    items = []
    ix_url = 'http://ixirc.com/api/'
    if query == '**just_search**':
        query = plugin.keyboard()
    results = requests.get(ix_url + '?q=%s&pn=%s' % (query,
                                                     page)).json()
    total_pages = results['pc']
    plugin.log.info('RESULTS %s', results)
    results = results['results']
    idx = 0
    tsys = copy.copy(hf.traditional)
    tsys = [(tsys[-3][0], '')]
    for item in results:

        try:
            size = item['szf']
            rsize = [float(size[:-3]) * x[0] for x in hf.alternative if x[1] == size[-3:]][0]
            log('Size %s' % rsize)
            items.append({
                'label': item['name'] + ' || Size : %s' % item['szf'],
                'info': {'title': item['name'],
                         'plot': 'Size: %s Network: %s Channel: %s Bot: %s' % (
                             item['szf'], item['nname'], item['cname'], item['uname'])},
                'path': plugin.url_for(
                    'stream',
                    download=hf.size(rsize, tsys).replace(' MB', ''),
                    server=item['naddr'],
                    channel=item['cname'],
                    bot=item['uname'],
                    packetId=item['n'],
                    filename=item['name'],
                ),
                'is_playable': True,
                'context_menu': [('Assign Metadata',
                                  actions.update_view(plugin.url_for(
                                      'assign_metadata',
                                      id=idx,
                                      search_term=query,
                                      page=page,
                                      from_XG='IX',
                                      name=False,
                                      bot=False,
                                      cache=False,
                                  ))), ('Just Download',
                                        actions.background(plugin.url_for(
                                            'stream',
                                            download=True,
                                            server=item['naddr'],
                                            channel=item['cname'],
                                            bot=item['uname'],
                                            packetId=item['n'],
                                            filename=item['name'],
                                        ))), ('Delete File',
                                              actions.background(plugin.url_for('delete_file'
                                                                                , name=item['name'], all_files=False))),
                                 ('Delete All Files',
                                  actions.background(plugin.url_for('delete_file'
                                                                    , name=item['name'], all_files=True)))],
            })
        except:
            continue
        try:
            if str(idx) == str(id):
                plugin.log.info('SUCCESS')
                items[idx]['info'] = labs
                items[idx]['thumbnail'] = labs['cover_url']
                items[idx]['properties'] = \
                    {'Fanart_Image': labs['backdrop_url']}
        except:
            pass
        plugin.log.info('IDX INFO %s' % items[idx]['info'])
        idx += 1
    if page < total_pages:
        items.append({'label': 'Next Page >>',
                      'path': plugin.url_for('search_ix', query=query,
                                             page=str(page + 1))})
    return items


@plugin.route('/just_download/<url>/<data>')
def just_download(url, data=None):
    if data is None:
        data = {}
    if str(data) != 'False':
        headers['Content-Type'] = 'application/json'
        r = requests.put(url, headers=headers, data=json.dumps(data))
    else:
        r = requests.post(url, headers=headers, data=data)
    plugin.log.info('''URL %s
 DATA %s
 STATUS CODE %s
 TEXT %s'''
                    % (r.url, data, r.status_code, r.text))


@plugin.route('/assign_metadata/<id>/<search_term>/<page>/<name>/<bot>/<from_XG>/<cache>'
              )
def assign_metadata(
        id,
        search_term,
        page,
        name=False,
        bot=False,
        from_XG=False,
        cache=False,
):
    plugin.log.info('NAME %s \n BOT %s CACHE: %s' % (name, bot,
                                                     str(cache)))
    if cache != 'nope':
        meta_cache = plugin.get_storage('meta_cache')
        if str(cache) == 'False':
            labs = get_meta()
            meta_cache = labs
        # plugin.log.info('META_CACHE %s' % meta_cache)
        elif cache == 'reapply':
            labs = table.find_one(latest='latest')
            log('META_CACHE: %s' % pp(labs))
        elif cache == 'next' or cache == 'prev':
            showcache = plugin.get_storage('showcache')
            index = showcache['last']['index']
            log('CURRENT EP INDEX %s' % index)
            index = index + 1 if cache == 'next' else index - 1
            episode = SEP(**showcache['last']['data'][1][index])
            showcache['last']['index'] = index
            try:
                labs = transform_ep_object(episode)
            except Exception, e:
                log(e)
            labs['TVShowTitle'] = showcache['last']['title']
            labs['backdrop_url'] = showcache['last']['data'][0]['fanart_url']
        elif cache != name:
            labs = file_meta(cache)
        if str(from_XG) == 'HI':
            return hi10eps(show=search_term, url=name, labs=labs, id=id)
        elif str(from_XG) == 'True':
            plugin.log.info('GOING THROUGH XG')
            return search(search_term=search_term, page=page, id=id,
                          labs=labs)
        elif str(from_XG) == 'IX':
            plugin.log.info('GOING THROUGH IX')
            return search_ix(query=search_term, page=page, id=id, labs=labs)
        elif str(name) != 'False':
            plugin.log.info('GOING THROUGH LIST_PACKLIST')
            return list_packlist(
                name=name,
                search_term=search_term,
                bot=bot,
                page=page,
                labs=labs,
                id=id,
                cache='nope'
            )



        # @plugin.route('/enter_custom/')........
        # def enter_custom():
        # server = plugin.keyboard(heading='Enter server (Ex: irc.server.net)')
        # channel = plugin.keyboard(heading = 'Enter channel (Ex: #channel)')
        # bot = plugin.keyboard(heading = 'Enter bot name')
        # packetId = plugin.keyboard(heading = 'Enter Packet Number')
        # filename = plugin.keyboard(heading = 'Enter file name (Ex: Movie.mkv)')
        # return stream(server=server,channel=channel,bot=bot,packetId=packetId,filename=filename)


@plugin.route('/haruhichan/<key>/<doMeta>/<filename>', name='haru')
@plugin.route('/haruhichan/<key>/')
def haruhichan(key='None', filename='', doMeta='F'):
    url = 'http://intel.haruhichan.com/?s='
    server = 'irc.rizon.net'
    channel = 'intel'
    items = []
    if key == 'None':
        key = plugin.keyboard(heading='Enter Search Term')
    if doMeta == 'T':
        labs = get_meta()
    soup = BS(scraper.get(url + key).text)
    results = soup.findAll(attrs={'class': re.compile('noselect')})
    for pack in results:
        p = pack.findAll('td')
        bot = p[0].text
        id = p[1].text
        name = p[4].string
        size = p[3].text
        item = {'label': '%s || %s || %s' % (name, size, bot),
                'path': plugin.url_for(
                    'stream',
                    download=False,
                    server=server,
                    channel=channel,
                    bot=bot,
                    packetId=id,
                    filename=name,
                ), 'context_menu': [('Assign Metadata',
                                     actions.update_view(plugin.url_for('haru'
                                                                        , doMeta='T', filename=name,
                                                                        key=key))), ('Just Download',
                                                                                     actions.background(plugin.url_for(
                                                                                         'stream',
                                                                                         download=True,
                                                                                         server=server,
                                                                                         channel=channel,
                                                                                         bot=bot,
                                                                                         packetId=id,
                                                                                         filename=name,
                                                                                     ))), ('Delete File',
                                                                                           actions.background(
                                                                                               plugin.url_for(
                                                                                                   'delete_file',
                                                                                                   name=name,
                                                                                                   all_files=False))),
                                    ('Delete All Files',
                                     actions.background(plugin.url_for('delete_file',
                                                                       name=name, all_files=True)))]}
        if name == filename:
            item['info'] = labs
            item['thumbnail'] = labs['cover_url']
            item['properties'] = {'Fanart_Image': labs['backdrop_url']}
        items.append(item)
    return items


@plugin.route('/webpages/xweasel/<query>/<page>')
def xweasel(query='lala', page='1'):
    # log('Table %s'% pp(list(table.all())))
    # return
    global network
    lastsearch = plugin.get_storage('lastsearch')
    log('PAGE %s QUERY %s' % (page, query))
    page = int(page)
    if query == 'lala':
        query = plugin.keyboard(heading='Search', default=lastsearch['last'])
    lastsearch['last'] = query
    xrequest = plugin.get_storage('%s_%s' % (query, page), ttl=60)
    if len(xrequest.keys()) == 0:
        r1 = requests.get('http://www.xweasel.org/Search.php?Description=%s&Page=%s' % (query, page))
        log("Request %s" % r1.status_code)
        soup = BS(r1.text)
        pages = len(soup.findAll('center')[-1].findChildren()) - 2
        xrequest['pages'] = pages
        results = soup.findAll('tr', attrs={'class': re.compile('row')})
        log('RESULTS %s' % len(results))
        if len(results) == 0: return
        mtitle = (lambda x: re.findall(re.compile(r'(.*?[ .]\d{4})[ .a-zA-Z]*'),
                                       re.sub(r'(\w*)([\\()\\](\b\w*)\S)', '', x))[0])
        items = []
        idx = 0
        for item in results:

            try:
                i = list(eval(item['onmouseover'].replace('ShowToolTip', '')))
                i = [x for x in i if x != '' and x != ' (Ready)' and x != ' (Full)' and x != ' (0/50)']
                i = i[:-1]
                filename, network, channel, bot, pack = i
            except Exception, e:
                log('ERROR: %s %s' % (e, list(eval(item['onmouseover'].replace('ShowToolTip', '')))))
            try:
                title = mtitle(filename)
                title = title.replace('.', ' ')
            except:
                title = filename
            network = 'irc.{}.net'.format(network)
            log('NETWORK %s' % network)
            log('Movie Item Title: %s' % title)
            size = item.findAll('td')[1].text.replace(r'&nbsp;', ' ')
            speed = item.findAll('td')[4].text.replace(r'&nbsp;', ' ')

            log('Item Stats: Speed %s, Size %s' % (speed, size))
            realsize = [float(size[:-3]) * x[0] for x in hf.alternative if x[1] == size[-3:]][0]
            tsys = copy.copy(hf.traditional)
            tsys = [(tsys[-3][0], '')]
            mlabs = {}
            if title != filename:
                mlabs['Size'] = realsize
                mlabs['Album'] = speed
                mlabs['Artist'] = [bot]
                mlabs['Genre'] = str(channel)
                # mlabs['plot'] = '\n FILENAME {} \n CHANNEL {} \n BOT {} \n SPEED {} \n SIZE {}'.format(filename,channel,bot,speed,size)
                # mlabs['Plot'] = str(filename + ' || Size: ' + size +' || Bot : ' + bot + ' || Speed: '+speed)
                c = copy.copy(movie_meta(title))
                c['plot'] += '\n {} \n CHANNEL {} \n BOT {} \n SPEED {} \n SIZE {}'.format(filename, channel, bot,
                                                                                           speed, size)
                mlabs.update(c)
                item = {
                    'label': str(filename + ' || Size: ' + size + ' || Bot : ' + bot + ' || Speed: ' + speed),
                    'path': plugin.url_for(
                        'stream',
                        download=hf.size(realsize, tsys).replace(' MB', ''),
                        server=network,
                        channel=channel,
                        bot=bot,
                        packetId=pack,
                        filename=filename,
                    ),
                    'is_playable': True,
                    'context_menu': [('Assign Metadata',
                                      actions.update_view(plugin.url_for(
                                          'assign_metadata',
                                          id=idx,
                                          search_term=query,
                                          page=page,
                                          name=filename,
                                          bot=bot,
                                          from_XG=False,
                                          cache=False,
                                      ))), ('Reapply Metadata',
                                            actions.update_view(plugin.url_for(
                                                'assign_metadata',
                                                id=idx,
                                                search_term=query,
                                                page=page,
                                                name=filename,
                                                bot=bot,
                                                from_XG=False,
                                                cache=True,
                                            ))), ('Just Download',
                                                  actions.background(plugin.url_for(
                                                      'stream',
                                                      download=True,
                                                      server=network,
                                                      channel=channel,
                                                      bot=bot,
                                                      packetId=pack,
                                                      filename=filename,
                                                  ))), ('Delete File',
                                                        actions.background(plugin.url_for('delete_file'
                                                                                          , name=filename,
                                                                                          all_files=False))),
                                     ('Delete All Files',
                                      actions.background(plugin.url_for('delete_file'
                                                                        , name=filename, all_files=True)))],
                    'info': mlabs if mlabs else '',
                    'thumbnail': mlabs['thumb'] if mlabs else '',
                    'properties': {'Fanart_Image': mlabs['backdrop_url']}
                }
            items.append(item)
            try:
                if str(idx) == str(id):
                    items[idx]['info'] = labs
                    items[idx]['thumbnail'] = labs['cover_url']
                    items[idx]['properties'] = \
                        {'Fanart_Image': labs['backdrop_url']}
            except:
                pass
            log('ITEMS %s' % len(items))
            idx += 1
        xrequest['data'] = items
    if page < xrequest['pages']:
        xrequest['data'].append({'label': 'Next Page >>',
                                 'path': plugin.url_for('xweasel', query=query,
                                                        page=str(page + 1))})
    log('ITEMS %s' % len(xrequest['data']))

    plugin.finish(items=xrequest['data'], sort_methods=['Size', 'Album', 'Genre', 'Artist'])


# @plugin.cached()
def movie_meta(title):
    # cacheMovie = plugin.get_storage(title)
    # if len(cacheMovie.keys()): return cacheMovie['labs']
    sqtitle = table.find_one(stitle=title)
    if sqtitle:
        log('FUCK YEAH')
        return sqtitle
    headers = {'Content-Type': 'application/json',
               'trakt-api-version': '2',
               'trakt-api-key': '05bcd2c0baf2685b8c196162d099e539033c21f7aa9fe1f87b234c2d62c2c1e4'}
    results = \
        requests.get('https://api-v2launch.trakt.tv/search?query=%s&type=movie'
                     % title[:-5], headers=headers).json()
    yr = title[-4:]
    plugin.log.info('Results %s' % pp(results))
    if len(results) == 0: return
    Movie = results[0]['movie']
    img_url = 'http://webservice.fanart.tv/v3/movies/%s?api_key=%s' % (Movie['ids']['imdb'], FA_api)
    plugin.log.info('Movie: %s' % pp(Movie))
    infoLabels = {}
    img_dat = requests.get(img_url).json()
    log('IMAGE DATA: %s' % pp(img_dat))
    try:
        infoLabels['poster'] = img_dat['movieposter'][0]['url']
    except:
        infoLabels['poster'] = ''

    try:
        infoLabels['cover_url'] = img_dat['movieposter'][0]['url']
    except:
        infoLabels['cover_url'] = ''
    try:
        infoLabels['plot'] = Movie['overview']
    except:
        infoLabels['plot'] = ''
    try:
        infoLabels['backdrop_url'] = img_dat['moviebackground'][0]['url']
    except:
        infoLabels['backdrop_url'] = ''
    try:
        infoLabels['year'] = Movie['year']
    except:
        infoLabels['year'] = ''
    try:
        infoLabels['title'] = Movie['title']
    except:
        infoLabels['title'] = ''
    try:
        infoLabels['thumb'] = img_dat['moviethumb'][0]['url']
    except:
        infoLabels['thumb'] = ''
    try:
        infoLabels['banner'] = img_dat['moviebanner'][0]['url']
    except:
        infoLabels['banner'] = ''
    try:
        infoLabels['fanart'] = img_dat['moviebackground'][0]['url']
    except:
        infoLabels['fanart'] = ''
    try:
        infoLabels['clearart'] = img_dat['hdmovieclearart'][0]['url']
    except:
        infoLabels['clearart'] = ''
    try:
        infoLabels['clearlogo'] = img_dat['hdmovieclearlogo'][0]['url']
    except:
        infoLabels['clearlogo'] = ''
    # cacheMovie['labs']             = infoLabels
    infoLabels['stitle'] = title
    table.upsert(infoLabels, ['stitle'])
    return infoLabels


@plugin.route('/hi10/', name='cloud10', options={'term': ''})
def hi10(term):
    last = plugin.get_storage('lastsearch')
    if not term:
        term = plugin.keyboard(heading='Search', default=last['last'])
    items = []

    url = 'http://hi10anime.com/?s=%s' % term
    u = requests.get(url)
    log(u.status_code)
    soup = BS(u.text)
    results = soup.findAll(attrs={'class': 'entry-title'})
    for r in results:
        show = r.parent.find('a').text
        link = r.a['href']
        title = r.a.text
        item = {
            'label': title,
            'path': plugin.url_for('hi10eps', url=link, show=show),
            'info': {'TVShowTitle': show}
        }
        items.append(item)
    return items


# @plugin.cached()
def hi_login(url):
    log_url = 'https://hi10anime.com/wp-login.php'
    hiuser = plugin.get_setting('hiusr', str)
    hipwd = plugin.get_setting('hipwd', str)
    data = {
        'log': hiuser,
        'pwd': hipwd
    }
    sess = scraper
    s = sess.post(log_url, data=data)
    log("Status: %s" % s.status_code)
    return sess.get(url).text


@plugin.route('/hi10eps/<show>/<url>')
def hi10eps(show, url, id=None, labs=None):
    soup = BS(hi_login(url))
    bc = soup.findAll(attrs={'class': 'showLinksTable'})#soup.findAll(attrs={'class': 'postMakerTABLE'})
    typ = 'column'
    try:
        eptest = bc[2].findAll(attrs={'class': 'postMakerTR'})[2:]
    except Exception, ed:
        # log(e.__dict__)
        log('ERROR %s LINE: %s' % (ed, sys.exc_info()[2].tb_lineno))
        eptest = soup.findAll('a', href=re.compile('mkv'))
        typ = 'single'
    try:
        aid = soup.find('a', attrs={'title': 'AniDB'})
        aid = aid['href'].split('aid=')[1]
    except Exception, ed:
        # log(e.__dict__)
        log('ERROR %s LINE: %s' % (ed, sys.exc_info()[2].tb_lineno))
        aid = ''
    items = []
    img = soup.find('p').img['src']
    idx = 0
    prev_link = ''
    for e in eptest:
        if typ == 'column':
            link = e.find('a')['href']
            link = 'https://' + link[link.find('hi10'):]
            c = [x for x in e.contents if x != '\n']
            episode = c[1].text.split('v')[0]
        else:
            link = e['href']
            link = 'https://' + link[link.find('hi10'):]
            episode = e.previous.previous
        if link == prev_link:
            continue
        prev_link = link
        try:
            episode = int(episode)
            info = gethimeta(episode, show, aid)
            label = info['title']
        except Exception, e:
            log('ERROR %s LINE: %s' % (e, sys.exc_info()[2].tb_lineno))
            try:
                fname = link.rsplit('/')[-1][:-4]
                log(fname)
                info = file_meta(fname)
                label = info['title']
            except Exception, f:
                log('ERROR %s LINE: %s' % (f, sys.exc_info()[2].tb_lineno))
                label = link.rsplit('/')[-1][:-4]
                info = {'TVShowTitle': show, 'cover_url': img, 'backdrop_url': img}
        try:
            if str(idx) == str(id) and labs:
                info = labs
        except Exception, e:
            log('ERROR %s LINE: %s' % (e, sys.exc_info()[2].tb_lineno))

        item = {
            'label': label,
            'path': link,
            'info': info,
            'thumbnail': info['cover_url'],
            'context_menu': [('Assign Metadata',
                              actions.update_view(plugin.url_for(
                                  'assign_metadata',
                                  id=idx,
                                  search_term=show,
                                  page=False,
                                  name=url,
                                  bot=False,
                                  from_XG='HI',
                                  cache=False,
                              ))), ('Reapply Metadata',
                                    actions.update_view(plugin.url_for(
                                        'assign_metadata',
                                        id=idx,
                                        search_term=show,
                                        page=False,
                                        name=url,
                                        bot=False,
                                        from_XG='HI',
                                        cache='reapply',
                                    ))), ('Next Episode',
                                          actions.update_view(plugin.url_for(
                                              'assign_metadata',
                                              id=idx,
                                              search_term=show,
                                              page=False,
                                              name=url,
                                              bot=False,
                                              from_XG='HI',
                                              cache='next',
                                          ))), ('Previous Episode',
                                                actions.update_view(plugin.url_for(
                                                    'assign_metadata',
                                                    id=idx,
                                                    search_term=show,
                                                    page=False,
                                                    name=url,
                                                    bot=False,
                                                    from_XG='HI',
                                                    cache='prev',
                                                )))],
            'properties': {'Fanart_Image': info['backdrop_url']},
            'info_type': 'video',
            'is_playable': True}
        idx += 1

        log(pp(item))
        items.append(item)
    for i in items:
        log(i['path'])
    return items


def gethimeta(episode, show, aid=''):
    shw = plugin.get_storage(show)
    if 'anidb' not in shw.keys() and aid:
        log('REQUESTING ANIDB DATA')
        r = requests.get(
            'http://api.anidb.net:9001/httpapi?request=anime&client=anidbtvdbmeta&clientver=1&protover=1&aid=%s' % aid)
        log("Status %s\n" % r.status_code)
        anitext = r.text
        shw['anidb'] = anitext
    else:
        anitext = shw['anidb']
    soup = BS(anitext)
    year = soup.find('startdate').text[:4]
    v = [x for x in soup.findAll('epno') if x.text == str(episode)][0]
    if 'shownep' not in shw.keys():
        title = ' '.join([show, year])
        log(title)
        id = api.get_matching_shows(show)
        log(id)
        shw['id'] = id[0][0]
        e = api.get_show_and_episodes(shw['id'])
        shw['shownep'] = [e[0].__dict__, [i.__dict__ for i in e[1]]]
    else:
        e = [SEP(**shw['shownep'][0]), [SEP(**i) for i in shw['shownep'][1]]]
    airdate = api.convert_date(v.parent.airdate.text)
    ep = [i for i in e[1] if
          2 >= (lambda x: x.days)(
              (airdate - api.convert_date(i.first_aired if i.first_aired else '1963-01-01'))) >= -2][0]
    try:
        info = transform_ep_object(ep)
    except Exception, e:
            log(e)
    info['TVShowTitle'] = e[0].name
    info['backdrop_url'] = e[0].fanart_url
    return info


if __name__ == '__main__':
    plugin.run()
