'''
    redditmusic.resources.lib.playlists
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains an xbmcswift2.Module for handling the playlists
    interaction for the addon.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import uuid
import functools
import kodiswift
from kodiswift import module, xbmc, xbmcgui, actions



def _run(plugin, endpoint, **items):
    '''Returns a RunPlugin string for use in a context menu.

    :param endpoint: The endpoint to be used with playlists.url_for().
    :param **items: Any keyword args to be passed to playlists.url_for().
    '''
    return actions.background(plugin.url_for(endpoint, **items))


class Playlists(object):
    '''Example usage::

        from xbmcswift2 import Plugin
        import xbcmswift2_playlists

        plugin = Plugin()
        lists = xbmcswift2_playlists.Playlists(plugin)

        @plugin.route('/')
        def index():
            items = [...]
            items.append(lists.get_show_playlists_item())

    :param plugin: A plugin instance.
    :param playlists_storage: The name to use for playlists storage.
    :param temp_item_storage: The name to use for temporary storage.
    :param replace_context_menu: Whether to clear the context menu before
                                 adding playlist specific items.

    '''

    def __init__(self, plugin, playlists_storage='my_playlists',
                 temp_item_storage='temp_items', replace_context_menu=True):
        self.plugin = plugin
        self.playlist_storage = 'my_playlists'
        self.temp_item_storage = 'temp_items'
        self.replace_context_menu = replace_context_menu
        self._run = functools.partial(_run, self.plugin)

        # register routes
        self.init_routes()

        # register a callback with swift
        self.plugin.before_add_items(self.add_ctx_to_playable_items)

    def _add(self, url_ptn, meth):
        name = meth.__name__
        self.plugin.add_url_rule(url_ptn, meth, name)

    def init_routes(self):
        self._add('/playlists/', self.show_playlists)
        self._add('/playlists/create/<code>/', self.create_playlist)
        self._add('/playlists/delete/<playlist>/', self.remove_playlist)
        self._add('/playlists/show/<name>/', self.show_playlist)
        self._add('/playlists/removeitem/<playlist>/<url>/', self.remove_from_playlist)
        self._add('/playlists/additem/<playlist>/<url>/', self.add_to_playlist)

    def _update_item_ctx(self, item, playlists):
        ctx = []
        for name in my_playlists.keys():
            label = 'Add to %s playlist' % name
            action = self._run('add_to_playlist', playlist=name, url=item['path'])
            ctx.append((label, action))
        if ctx:
            item['context_menu'] = ctx
            item['replace_context_menu'] = self.replace_context_menu

    def add_ctx_to_playable_items(self, items):
        my_playlists = self.plugin.get_storage(self.playlist_storage)
        for item in items:
            if item.get('is_playable'):
                self._update_item_ctx(item, my_playlists)
        return items

    def show_playlists(self):
        '''Displays the 'Create Playlist' item as well as items for any
        playlists the user has created.
        '''
        my_playlists = self.plugin.get_storage(self.playlist_storage)

        one_time_code = uuid.uuid4().hex
        create = {
            'label': 'Create Playlist',
            'path': self.plugin.url_for('create_playlist', code=one_time_code),
        }
        print create

        items = [{
            'label': name,
            'path': self.plugin.url_for('show_playlist', name=name),
            'context_menu': [('Delete this playlist',
                             self._run('remove_playlist', playlist=name)), ]
        } for name in sorted(my_playlists.keys())]

        return [create] + items

    def create_playlist(self, code):
        '''Creates a new empty user named playlist. User's can add playlist items
        from the context menu of playable items elsewhere in the addon.
        '''
        # This whole codes business is to prevent _create_playlist from being
        # called upon a Container.Refresh.
        codes = self.plugin.get_storage('codes')
        if code not in codes.keys():
            my_playlists = self.plugin.get_storage('my_playlists')
            name = self.plugin.keyboard(heading='Enter playlist name')
            if name:
                my_playlists.set_default(name, [])
            codes[code] = True
        return self.plugin.finish(self.show_playlists(), update_listing=True)

    def remove_playlist(self, playlist):
        '''Deletes a user specified playlist. If the playlist is not empty, the
        user will be presented with a yes/no confirmation dialog before deletion.
        '''
        my_playlists = self.plugin.get_storage('my_playlists')
        num_items = len(my_playlists[playlist])

        delete = True
        if num_items > 0:
            dialog = xbmcgui.Dialog()
            delete = dialog.yesno(self.plugin.name, 'Are you sure you wish to delete?')

        if delete:
            del my_playlists[playlist]
            my_playlists.sync()
            xbmc.executebuiltin('Container.Refresh')

    def show_playlist(self, name):
        '''Displays a user's custom playlist. The playlist items are persisted via
        plugin storage.
        '''
        my_playlists = self.plugin.get_storage(self.playlist_storage)
        items = my_playlists[name]

        # Augment the existing list items with a context menu item to 'Remove from
        # Playlist'.
        for item in items:
            ctx_items = [
                ('Remove this item from playlist',
                 self._run('remove_from_playlist', playlist=name, url=item['path']))
            ]
            item['context_menu'] = ctx_items

        return items

    def remove_from_playlist(self, playlist, url):
        '''Deletes an item from the given playlist whose url matches the provided
        url.
        '''
        # We don't have the full item in temp_items, so have to iterate over items
        # in the list and match on url
        my_playlists = self.plugin.get_storage('my_playlists')
        try:
            match = (item for item in my_playlists[playlist]
                     if item['path'] == url).next()
            my_playlists[playlist].remove(match)
            my_playlists.sync()
            xbmc.executebuiltin('Container.Refresh')
        except StopIteration:
            pass

    def add_to_playlist(self, playlist, url):
        '''Adds an item to the given playlist. The list item added will be pulled
        from temp_items storage and matched on the provided url.
        '''
        temp_items = self.plugin.get_storage('temp_items')
        item = temp_items[url]
        my_playlists = self.plugin.get_storage('my_playlists')
        my_playlists[playlist].append(item)
        my_playlists.sync()

    def get_show_playlists_item(self):
        return {
            'label': 'Show Playlists',
            'path': self.plugin.url_for('show_playlists'),
        }
