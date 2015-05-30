from xbmcswift2 import Plugin
import os
import sys
import re
import json
import xbmc,xbmcaddon,xbmcplugin
import xbmcgui
import threading
from urllib2 import Request,urlopen
import glob


plugin = Plugin()

# lib = os.path.join(plugin._addon_id, 'resources', 'lib' )
# print lib
lib = 'special://home' + '/addons/' + plugin._addon_id
lib = xbmc.translatePath(lib)
print lib
lib = os.path.join( lib, 'resources', 'lib')
print lib
sys.path.append(lib)

sys.path.append (xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) ))

import urllib
import requests
from xbmcswift2 import actions

import thetvdbapi, MovieMeta
api = thetvdbapi.TheTVDB()
movie_meta = MovieMeta.TMDB()


api_key = plugin.get_setting('api_key' ,str)
api_key = api_key.replace(' ','')

plugin.log.info('API Key ' +api_key)

headers = {'Authorization': api_key}

api_url = 'http://%s:%s/api/1.0/' % (plugin.get_setting('host',str),plugin.get_setting('port',str))

tmp_path = plugin.get_setting('tmp_path' ,str)
tmp_path += "*.*"
dl_path = plugin.get_setting('xg_dl_path',str)
dl_path+='*.*'



#Fix for smb paths
try:
	tmp_user = re.search('//(.+?)/',tmp_path).group(1)
	dl_user = re.search('//(.+?)/',dl_path).group(1)
	tmp_path = tmp_path.replace('smb://%s'%tmp_user,r'\\%s' % plugin.get_setting('host',str))
	dl_path = dl_path.replace('smb://%s' % dl_user,r'\\%s' % plugin.get_setting('host',str))
except: plugin.log.info('error')

plugin.log.info('TMP_PATH %s \n DL_PATH %s' % (tmp_path,dl_path))

@plugin.route('/')
def index():
	items = [{
		'label': 'Search XG...',
		'path': plugin.url_for('search',search_term = 'first_page',page = '1'),
		'is_playable': False
	}, {'label':'Play Downloading File', 'path': plugin.url_for('play_local_file'),'is_playable': True},
	{
		'label' : 'Webpage Parsers',
		'path' : plugin.url_for('parsers')}]
	return items
@plugin.route('/search/<search_term>/<page>/')
def search(search_term='first_page',page = '1',id=None, labs = None):
	# packs = xdcc_search.get_packs('http://xdcc.horriblesubs.info','naruto')
	# plugin.log.info('Packs' + str(packs))
	 #%s.%s?searchTerm=%s' % (port,type,format,searchTerm)
	if search_term == 'first_page':
		keyboard = xbmc.Keyboard('','Enter Search Term',False)
		keyboard.doModal()
		if keyboard.isConfirmed(): search_term = keyboard.getText()
	search_packets = 'packets.json?searchTerm=%s&maxResults=20&page=%s' % (search_term,page)
	request = requests.get(api_url+search_packets,headers=headers)
	results = request.json()
	
	# results = json.loads(results)
	items=[]
	idx = 0
	for option in results['Results']:
		guid_url = api_url + 'packets/%s/enable.json' % (option['Guid'])
		item = {'label':option['Name'],'path':plugin.url_for('play_file',url=guid_url,name=option['Name']),'is_playable':True, 'context_menu':[('Assign Metadata',actions.update_view(plugin.url_for('assign_metadata',id = idx,search_term = search_term,page = page,from_XG = True, name = False, bot = False))),('Just Download',actions.background(plugin.url_for('just_download',url = guid_url,data = {})))]}
		try:
			if str(idx) == str(id):
				items[idx]['info'] = labs
				items[idx]['thumbnail'] = labs['cover_url']
				items[idx]['properties'] = {'Fanart_Image':labs['backdrop_url']}
		except: pass
		items.append(item.copy())
		idx+=1
	items.append({'label' : 'Next Page >>' , 'path' : plugin.url_for('search',search_term = search_term,page = str(int(page) + 1))})
	return plugin.finish(items)
	
@plugin.route('/play/<name>/<url>/')
def play_file(name,url,data = {}):
	plugin.log.info('Url is: %s' % url)
	#Check to see if file already exists
	tmp_files = glob.glob(tmp_path)
	tmpName = re.sub(r'[\W_]+','',name)
	tmpName = tmpName.lower()
	dl_file = False
	local_url = ''
	plugin.log.info('Temp Name is' + tmpName)
	dl_files = glob.glob(dl_path)
	for filename in dl_files:
		plugin.log.info('Filepath is ' + filename)
		if re.sub(r'[\W_]+','',name) in re.sub(r'[\W_]+','',filename):
			local_url = filename
			dl_file = True
			break
	if local_url == '':
		for filename in tmp_files:
			plugin.log.info('Filepath is ' + filename)
			if tmpName in filename:
				local_url = filename
				break
		
	
	
	# Work around for seeing if it is still downloading
	notUsing = True
	if local_url and not dl_file:
		try:
			os.rename(local_url,local_url+"_")
			notUsing = True
			os.rename(local_url+"_",local_url)
		except OSError as e:
			notUsing = False
	if local_url != '' and not notUsing or dl_file:
		# if manual_meta: 
			# infoLabels  = get_meta()
			# item = {'info':infoLabels, 'path' : local_url , 'icon' : infoLabels['cover_url'], 'thumbnail' : infoLabels['cover_url']}
			# plugin.set_resolved_url(item)
		# else:
		plugin.set_resolved_url(local_url)
	else:
		if data:
			headers['Content-Type'] = 'application/json'
			r = requests.put(url,headers = headers, data = json.dumps(data))
			plugin.log.info('Url is %s \n Data is %s \n Status is %s \n Text is %s' % (r.url,data,r.status_code,r.text))
		else: r = requests.post(url,headers=headers)	
		
		# if manual_meta: infoLabels  = get_meta()
		# else: infoLabels = {'title' : name,'cover_url':''}
		dialog = xbmcgui.DialogProgress()
		dialog.create('Streaming file', 'Buffering file before playing...')
		progress = 0
		buffering_time = int(float(30))
		plugin.log.info("buffering_time="+str(buffering_time))
		dialog.update(progress)
		
		
		cancelled=False
		while progress <= buffering_time:
			dialog.update(int( float(float(progress) / float(buffering_time))*100 ) )
			
			#######################################################################################################################
			#xbmc.sleep(10000)
			xbmc.sleep(1000)
			#######################################################################################################################
			
			progress = progress + 1
			plugin.log.info("progress="+str(progress))
			if dialog.iscanceled():
				cancelled=True
				break

		dialog.close()
		tmp_files = glob.glob(tmp_path)
		tmpName = re.sub(r'[\W_]+','',name)
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
	tmp_files = glob.glob(tmp_path)
	keyboard = xbmc.Keyboard('','Enter File Name',False)
	keyboard.doModal()
	if keyboard.isConfirmed(): name = keyboard.getText()
	
	names = name.strip()
	local_url = ''
	for filename in tmp_files:
		plugin.log.info('Filepath is ' + filename)
		for term in names:
			if term in filename:
				allTerms = True
				break
			else: 
				allTerms = False
				break
		if allTerms:	local_url = filename
	if local_url == '':
		dialog = xbmcgui.Dialog()
		dialog.notification(message = 'Could Not find file')
	plugin.log.info('Playing url: %s' % local_url)
	item = {'path':local_url,'label':name}
	
	plugin.set_resolved_url(local_url)
	

@plugin.route('/webpages/')
def parsers():
	items = [{'label' : 'Add a Channel...',	'path' : plugin.url_for('add_server')},{'label' : 'Search ixIRC...', 'path' : plugin.url_for('search_ix',query = '**just_search**',page = '0')}]
	plugin.log.info('List Storage %s ' % plugin.list_storages())
	for storage in plugin.list_storages() :
		storage = plugin.get_storage(storage)
		plugin.log.info('Storage %s' % storage)
		items.append({'label' : storage['name'], 'path':plugin.url_for('channel',name = storage['name']), 'context_menu' : [('Refresh Packlist',actions.background(plugin.url_for('refresh',name=storage['name'])))]})
	return items

@plugin.route('/add_server/')
def add_server():
	keyboard = xbmc.Keyboard('','Enter Host Server (Ex: irc.server.net)',False)
	keyboard.doModal()
	if keyboard.isConfirmed(): server = keyboard.getText()
	keyboard = xbmc.Keyboard('','Enter Channel Name',False)
	keyboard.doModal()
	if keyboard.isConfirmed(): name = keyboard.getText()
	channel = plugin.get_storage('%s' % (name))
	channel['name'] = name
	keyboard = xbmc.Keyboard('','Enter Webpage Url (Ex: http://xdcc.channel.com/',False)
	keyboard.doModal()
	if keyboard.isConfirmed(): url = keyboard.getText()
	packlist = get_packlist(url)
	channel['url'] = url
	channel['server'] = server
	channel['packlist'] = packlist
	channel['bots'] = []
	return parsers()
	
@plugin.route('/webpages/<name>/')
def channel(name):
	items = []
	items = [{ 'label': 'Search Packlist...', 'path':plugin.url_for('search_channel',name = name, bot = 'list_all')}, { 'label' : 'List All Packlist', 'path':plugin.url_for('list_packlist',name = name,search_term = 'list_all',bot = 'list_all',page = '1')}, {'label':'List Bots','path':plugin.url_for('list_bots',channel = name)}]
	return items

	

@plugin.route('/webpages/<name>/list_packlist/<bot>/<search_term>/<page>')
def list_packlist(name,search_term='list_all',bot = 'list_all',page = '1',labs={},id=''):
	page = int(page)
	cache = plugin.get_storage('%s' %(name))
	packlist = cache['packlist']
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
				if term.lower() in i['filename'].lower(): all_Terms = True
				else: 
					all_Terms = False
					break
			if all_Terms:
				search_packlist.append(i)
		idx = 0
		for item in search_packlist[prev:curr]:
			items.append({'label':item['filename'] + ' || Size: ' + str(item['size']) + ' MB || Bot : ' + item['bot'],'path':plugin.url_for('stream',download = False, server = cache['server'],channel = name,bot = item['bot'],packetId = item['packetId'], filename = item['filename']),'is_playable': True, 'context_menu' : [('Assign Metadata',actions.update_view(plugin.url_for('assign_metadata',id = idx,search_term = search_term,page = page,name = name,bot=bot, from_XG = False))),('Refresh Packlist',actions.background(plugin.url_for('refresh',name=name))),('Just Download',actions.background(plugin.url_for('stream',download = True,server = cache['server'],channel = name,bot = item['bot'],packetId = item['packetId'], filename = item['filename']))),('Delete File',actions.background(plugin.url_for('delete_file',name=item['filename'],all_files = False))),('Delete All Files',actions.background(plugin.url_for('delete_file',name=item['filename'],all_files = True)))]})
			try:
				if str(idx) == str(id):
					items[idx]['info'] = labs
					items[idx]['thumbnail'] = labs['cover_url']
					items[idx]['properties'] = {'Fanart_Image':labs['backdrop_url']}
			except: pass
			idx+=1
	else: 
		idx = 0
		for item in packlist[prev:curr] :
			plugin.log.info('ITEM %s' % item)
			items.append({'label':item['filename'] + ' || Size: ' + str(item['size']) + ' MB || Bot : ' + item['bot'],'path':plugin.url_for('stream',download = False, server = cache['server'],channel = name,bot = item['bot'],packetId = item['packetId'], filename = item['filename']),'is_playable': True, 'context_menu' : [('Assign Metadata',actions.update_view(plugin.url_for('assign_metadata',id = idx,search_term = search_term,page = page,name = name,bot=bot, from_XG = False))),('Refresh Packlist',actions.background(plugin.url_for('refresh',name=name))),('Just Download',actions.background(plugin.url_for('stream',download = True,server = cache['server'],channel = name,bot = item['bot'],packetId = item['packetId'], filename = item['filename']))),('Delete File',actions.background(plugin.url_for('delete_file',name=item['filename'],all_files = False))),('Delete All Files',actions.background(plugin.url_for('delete_file',name=item['filename'],all_files = True)))]})
			try:
				if str(idx) == str(id):
					items[idx]['info'] = labs
					items[idx]['thumbnail'] = labs['cover_url']
					items[idx]['properties'] = {'Fanart_Image':labs['backdrop_url']}
			except: pass
			idx+=1
	if curr <= len(packlist):
		items.append({'label':'Next Page >>', 'path' : plugin.url_for('list_packlist',name = name,search_term = search_term,bot = bot, page = str( page + 1))})
	if page > 1:
		items.insert(0,{'label' : '<< Previous Page' , 'path' : plugin.url_for('list_packlist',name = name,search_term = search_term,bot = bot,page = str( page - 1))})
	return items	

@plugin.route('/webpages/<name>/search/<bot>/')
def search_channel(name,bot = 'all_bots'):
	keyboard = xbmc.Keyboard('','Enter Search Term',False)
	keyboard.doModal()
	if keyboard.isConfirmed(): search_term = keyboard.getText()
	return list_packlist(name = name, search_term = search_term, page = '1', bot = bot)
	
	
@plugin.route('/webpages/<channel>/bots/')
def list_bots(channel):
	cache = plugin.get_storage(channel)
	packlist = cache['packlist']
	if cache['bots'] == []:
		for item in packlist:
			if item['bot'] not in str(cache['bots']):
				cache['bots'].append({'label':item['bot'], 'path':plugin.url_for('bots',channel = channel, bot = item['bot'])})
	
	return cache['bots']
	
	
@plugin.route('/webpages/<channel>/bots/<bot>/')
def bots(channel,bot):
	return [{'label': 'Search Bot Packlist', 'path':plugin.url_for('search_channel',name = channel, bot = bot)},{'label':'List All Packs for %s' % bot, 'path':plugin.url_for('list_packlist',name = channel, search_term = 'list_all',bot = bot, page = '1')}]

	
@plugin.route('/update_packlist/<name>/')
def refresh(name):
	storage = plugin.get_storage(name)
	storage['packlist'] = get_packlist(storage['url'])
	for item in storage['packlist']:
		if item['bot'] not in str(storage['bots']):
			storage['bots'].append({'label':item['bot'], 'path':plugin.url_for('bots',channel = channel, bot = item['bot'])})

	
def get_packlist(url):
	url += 'search.php'
	r = requests.get(url)
	plugin.log.info('Packlist Status %s' % r.status_code)
	text = r.text
	m = re.findall('= (.+?);\n',text)
	items = []
	for item in m:
		item = item.replace("b:","'bot':").replace("n:","'packetId':").replace("f:","'filename':").replace("s:","'size':")
		dict = eval(item)
		items.append(dict.copy())
	return items

@plugin.route('/stream/<download>/<server>/<channel>/<bot>/<packetId>/<filename>')
def stream(server,channel,bot,packetId,filename, download = False):
	if '#' not in channel:
		channel = '#' + channel
	data = {"server":server,"channel":channel,"bot":bot,"packetId":int(packetId),"packetName":filename}
	url = api_url + 'packets.json'
	if download == True: just_download(url,data)
	else: return play_file(filename,url,data)
	
def get_meta():
	dialog = xbmcgui.Dialog()
	optionlist = ['','']
	optionlist[0] = 'tvshow'
	optionlist[1] = 'movie'
	imdb = ''
	tvdb = ''
	tmdb = ''
	index = dialog.select('Choose Video Type',optionlist)
	stype = optionlist[index]
	search_meta = []
	option_list = []
	if stype == 'tvshow':
		keyboard = xbmc.Keyboard('','Enter a Title',False)
		keyboard.doModal()
		if keyboard.isConfirmed(): title = keyboard.getText()
		results = api.get_matching_shows(title)
		for item in results: 
			option={'tvdb_id':item[0],'title':item[1],'imdb_id':item[2]}; 
			search_meta.append(option)
		for option in search_meta:
			disptitle=option['title']
			option_list.append(disptitle)
		index=dialog.select('Choose',option_list)
		Show = search_meta[index]
		shownep = api.get_show_and_episodes(Show['tvdb_id'])
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
				season_list.append('Season %s Episodes (%s - %s)' % (option2,start_ep, end_ep))
		index = dialog.select('Choose Season',season_list)
		season = re.search('Season (.+?) Episodes',season_list[index]).group(1)
		episode_list = []
		plugin.log.info('SEASON' + season)
		for item in shownep[1]:
			if item.season_number == season:
				disptitle = '%sx%s (%s) %s' % (item.season_number,item.episode_number, item.absolute_number, item.name)
				episode_list.append(disptitle)
		index = dialog.select('Choose Episode',episode_list)
		episode = index + 1
		# keyboard = xbmc.Keyboard('','Enter a Season',False)
		# keyboard.doModal()
		# if keyboard.isConfirmed(): season = keyboard.getText()
		# keyboard = xbmc.Keyboard('','Enter an Episode',False)
		# keyboard.doModal()
		# if keyboard.isConfirmed(): episode = keyboard.getText()
		episode = api.get_episode_by_season_ep(Show['tvdb_id'],season,episode)
		infoLabels = transform_ep_object(episode)
		infoLabels['TVShowTitle'] = Show['title']
		imdb = Show['imdb_id']
		tvdb = Show['tvdb_id']
		img = infoLabels['cover_url']
	elif stype == 'movie':
		keyboard = xbmc.Keyboard('','Enter a Title',False)
		keyboard.doModal()
		if keyboard.isConfirmed(): title = keyboard.getText()
		results = movie_meta.tmdb_search(title)['results']
		plugin.log.info('Results %s' % results)
		for item in results: 
			if item['release_date']:
				year = item['release_date'][:4]
			option={'tmdb_id':item['id'],'title':item['title'],'year':year}
			search_meta.append(option)
		for option in search_meta:
			disptitle='%s (%s)' % (option['title'],option['year'])
			option_list.append(disptitle)
		dialog = xbmcgui.Dialog()
		index=dialog.select('Choose',option_list)
		Movie = search_meta[index]
		tmdb = Movie['tmdb_id']
		plugin.log.info(Movie)
		infoLabels = Movie
		
		plugin.log.info(infoLabels)

	# xbmc.log(str(trakt_tv))
	headers = {
	  'Content-Type': 'application/json',
	  'trakt-api-version': '2',
	  'trakt-api-key': '05bcd2c0baf2685b8c196162d099e539033c21f7aa9fe1f87b234c2d62c2c1e4'
	}
	if stype == 'movie': api_url = 'https://api-v2launch.trakt.tv/search?id_type=tmdb&id=%s' % (tmdb)
	else: api_url = 'https://api-v2launch.trakt.tv/search?id_type=tvdb&id=%s' % (tvdb)
	request = requests.get(api_url, headers=headers)
	plugin.log.info('TRAKT JSON %s' % request.json())
	if stype == 'tvshow':
		trakt_meta = request.json()[0]['show']
	else:
		trakt_meta = request.json()[0]['movie']
	plugin.log.info("Trakt_meta %s" % trakt_meta)
	if stype == 'tvshow': 
		infoLabels['TVShowTitle'] = trakt_meta['title']
		infoLabels['backdrop_url'] = trakt_meta['images']['fanart']['full']
	else: 
		infoLabels['title'] = trakt_meta['title']
		infoLabels['cover_url'] = trakt_meta['images']['poster']['medium']
		infoLabels['plot'] = trakt_meta['overview']
		infoLabels['backdrop_url'] = trakt_meta['images']['fanart']['full']
	return infoLabels

def transform_ep_object(episode):
	meta = {}
	meta['episode_id'] = episode.id
	meta['plot'] = api.check(episode.overview)
	if episode.guest_stars:
		guest_stars = episode.guest_stars
		if guest_stars.startswith('|'):
			guest_stars = guest_stars[1:-1]
		guest_stars = guest_stars.replace('|', ', ')
		meta['plot'] = meta['plot'] + '\n\nGuest Starring: ' + guest_stars
	meta['rating'] = float(api.check(episode.rating,0))
	meta['premiered'] = api.check(episode.first_aired)
	meta['title'] = api.check(episode.name)
	meta['poster'] = api.check(episode.image)
	meta['director'] = api.check(episode.director)
	meta['writer'] = api.check(episode.writer)
	meta['season'] = int(api.check(episode.season_number,0))
	meta['episode'] = int(api.check(episode.episode_number,0))
	meta['cover_url'] = api.check(episode.image)
	return meta

@plugin.route('/delete_file/<name>/<all_files>')	
def delete_file(name,all_files=False):
	plugin.log.info('NAME ' + name)
	tmp_files = glob.glob(tmp_path)
	dl_files = glob.glob(dl_path)
	if all_files:
		try:
			for file in dl_files:
				os.remove(file)
		except: pass
		try:
			for file in tmp_files:
				os.remove(file)
		except:pass
	tmpName = re.sub(r'[\W_]+','',name)
	tmpName = tmpName.lower()
	plugin.log.info('Temp Name is' + tmpName)
	try:
		for filename in tmp_files:
			plugin.log.info('Filepath is ' + filename)
			if tmpName in filename.lower():
				os.remove(filename)
	except: pass
	try:
		for filename in dl_files:
			if tmpName in re.sub(r'[\W_]+','',filename.lower()):
				os.remove(filename)
	except: pass
@plugin.route('/webpages/search_ix/<query>/<page>')
def search_ix(query = '**just_search**',page = '0',id = -1,labs = {}):
	page = int(page)
	items = []
	ix_url = 'http://ixirc.com/api/'
	if query == '**just_search**':
		query = plugin.keyboard()
	results = requests.get(ix_url + '?q=%s&pn=%s' % (query,page)).json()
	total_pages = results['pc']
	results = results['results']
	idx = 0
	for item in results:
		
		try:
			items.append({'label':item['name'] + ' || Size : %s' % item['szf'],'info':{'title': item['name'],'plot':'Size: %s \n Network: %s \n Channel: %s \n Bot: %s' % (item['szf'],item['nname'],item['cname'],item['uname'])},'path':plugin.url_for('stream',download = False,server = item['naddr'],channel = item['cname'], bot = item['uname'], packetId = item['n'],filename = item['name']), 'is_playable': True
			, 'context_menu' : [('Assign Metadata',actions.update_view(plugin.url_for('assign_metadata',id = idx,search_term = query,page = page,from_XG = False, name = False, bot = False))),('Just Download',actions.background(plugin.url_for('stream',download = True,server = item['naddr'],channel = item['cname'], bot = item['uname'], packetId = item['n'],filename = item['name']))),('Delete File',actions.background(plugin.url_for('delete_file',name=item['name'],all_files = False))),('Delete All Files',actions.background(plugin.url_for('delete_file',name=item['name'],all_files=True)))]})
		except: continue
		try:
			if str(idx) == str(id): 
				plugin.log.info("SUCCESS")
				items[idx]['info'] = labs
				items[idx]['thumbnail'] = labs['cover_url']
				items[idx]['properties'] = {'Fanart_Image':labs['backdrop_url']}
		except: pass
		plugin.log.info('IDX INFO %s' % items[idx]['info'])
		idx+=1
	if page < total_pages:
		items.append({'label':'Next Page >>','path':plugin.url_for('search_ix',query = query, page = str(page+1))})
	return items
	
@plugin.route('/just_download/<url>/<data>')
def just_download(url,data={}):
	if data:
		headers['Content-Type'] = 'application/json'
		r = requests.put(url,headers = headers, data = json.dumps(data))
	else: r = requests.post(url,headers=headers,data = data)
	plugin.log.info('URL %s \n DATA %s \n STATUS CODE %s \n TEXT %s' % (r.url,data,r.status_code,r.text))

@plugin.route('/assign_metadata/<id>/<search_term>/<page>/<name>/<bot>/<from_XG>')
def assign_metadata(id,search_term,page,name = False,bot=False, from_XG = False):
	plugin.log.info("NAME %s \n BOT %s" % (name,bot))
	labs = get_meta()
	if str(name) != 'False':
		plugin.log.info('GOING THROUGH LIST_PACKLIST')
		return list_packlist(name=name,search_term=search_term,bot=bot,page=page,labs=labs,id=id)
	elif str(from_XG) == 'True':
		plugin.log.info('GOING THROUGH XG')
		return search(search_term = search_term, page = page, id = id, labs = labs)
	else:
		plugin.log.info('GOING THROUGH IX')
		return search_ix(query=search_term,page = page,id = id,labs = labs)

if __name__ == '__main__':
	plugin.run()
	plugin.log.info('ARGS %s' % plugin.request.args)