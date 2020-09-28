# -*- coding: utf-8 -*-
import sys, json, re
import requests, urllib, urlparse
from bs4 import BeautifulSoup as BS
import xbmc, xbmcgui, xbmcaddon, xbmcplugin

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

xbmcplugin.setContent(addon_handle, 'videos')

my_addon = xbmcaddon.Addon('plugin.video.anime365')

acc_login = my_addon.getSetting('sa-login')
acc_paswd = my_addon.getSetting('sa-paswd')

main_url = 'https://smotret-anime.online'
local_type = my_addon.getSetting('local-type')

if local_type == 'Dub':
	local_type = '/ozvuchka'
else:
	local_type = '/russkie-subtitry'

def BuildUrlDirection(**kwargs):
	return "{0}?{1}".format(base_url, urllib.urlencode(kwargs))

def Message(title, message):
	xbmcgui.Dialog().ok(title, message)

def AddFolder(label, action, **kwargs):
	if 'icon' not in kwargs:
		kwargs.setdefault('icon', 'DefaultFolder.png')

	if 'info' not in kwargs:
		kwargs.setdefault('info', '')

	item = xbmcgui.ListItem(label)
	item_url = BuildUrlDirection(label = label, action = action, **kwargs)
	
	item.setArt({'poster': kwargs['icon'], 'banner': kwargs['icon'], 'icon': kwargs['icon']})

	item.setInfo('video', {'title': label, 'plot': kwargs['info']})

	xbmcplugin.addDirectoryItem(handle = addon_handle, url = item_url, listitem = item, isFolder = True)

def AccountSession():
	login_url = main_url + '/users/login'

	header = {
		u'User-Agent': u'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 YaBrowser/20.8.3.115 Yowser/2.5 Safari/537.36'
	}

	reSes = requests.Session()

	reSes.headers.update(header)

	csrf = BS(reSes.get(login_url).content, 'html.parser').find('input', type = 'hidden').attrs["value"]

	payload_data = {
		'csrf': csrf,
		'LoginForm[username]': acc_login,
		'LoginForm[password]': acc_paswd,
		'yt0': '',
		'dynpage': 1
	}
	
	lc = reSes.post(login_url, data = payload_data)

	cheak = BS(lc.content,'html.parser').find('li').text

	if 'E-mail' in cheak:
		Message('Account', 'Invalid E-Mail or password')
		return requests
	else:
		return reSes

Session = AccountSession()

def AccountID():
	account_result = Session.get(main_url)
	anime_information = BS(account_result.content, 'html.parser')

	return str(re.findall(r'\d+', anime_information.find_all('ul', class_ = 'dropdown-content')[1].find_all('a')[1].attrs['href'])[0])

AccID = AccountID()

def AnimeUrlFixer(bad_urls):
	fix_urls = []

	for i in range(len(bad_urls)-1):
		if bad_urls[i].attrs['href'] != bad_urls[i+1].attrs['href']:
			fix_urls.append(bad_urls[i].attrs['href'])

	return fix_urls

def PlayVideo(video_name, url, sub):
	Item = xbmcgui.ListItem(video_name, path = url)
	Item.setProperty('IsPlayable', 'true')

	if local_type == '/russkie-subtitry':
		Item.setSubtitles([sub])
		xbmc.Player().showSubtitles(True)

	xbmc.Player().play(item = url, listitem = Item)

def ExtractVideoData(episode_url):
	page_info = Session.get(main_url + episode_url)

	translation_url = BS(page_info.content, 'html.parser').find('iframe', id = 'videoFrame').attrs['src']

	translation_element = BS(Session.get(translation_url).content, 'html.parser').find('video')

	if translation_element != None:
		if local_type == '/russkie-subtitry':
			sub_url = translation_element.attrs['data-subtitles'].replace('?willcache', '')
			if sub_url == '':
				sub_url = ' '
		else:
			sub_url = ' '

		video_url = json.loads(translation_element.attrs['data-sources'])[0]['urls'][0]
	else:
		video_url = main_url + '/posters/11567.34575557493.jpg'
		sub_url = ' '

	return {'url': video_url, 'sub': sub_url}

def GenerateEpisodeList(page_url):
	episodes_result = Session.get(main_url + page_url)
	episodes_info = BS(episodes_result.content, 'html.parser').find_all('div', class_ = "col s12 m6 l4 x3")

	for data in episodes_info:
		AddFolder(data.find('a').text.replace('play_circle_filled', '').encode('utf-8'), 'anime_episode', episode_page_url = (data.find('a').attrs['href'] + local_type))

	xbmcplugin.endOfDirectory(addon_handle)

def GenerateLocalTeamList(episode_url):
	localteam_result = Session.get(main_url + episode_url)
	team_tablet = BS(localteam_result.content, 'html.parser').find_all('div', class_ = 'row')[2].find_all('a')

	for team in team_tablet:
		data = ExtractVideoData(team.attrs['href'])

		AddFolder(team.text.encode('utf-8'), 'video_episode', url = data['url'], sub = data['sub'])

	xbmcplugin.endOfDirectory(addon_handle)

def AnimeSearch():
	kb = xbmc.Keyboard()
	kb.setDefault('')
	kb.setHeading('Поиск')
	kb.doModal()

	if kb.isConfirmed():
		query = kb.getText()

		search_result = Session.get(main_url + '/catalog/search?page=1&q=' + str(query))
		anime_information = BS(search_result.content, 'html.parser')

		anime_names = anime_information.find_all('h2', class_ = 'line-1')
		anime_posters = anime_information.find_all('img')
		anime_plots = anime_information.find_all('div', class_ = 'm-catalog-item__description')
		anime_urls = AnimeUrlFixer(anime_information.find_all('a', rel = 'nofollow'))

		for i in range(len(anime_names)):
			anime_poster = main_url + anime_posters[i].attrs['src']

			if Session.get(anime_poster).status_code == 404:
				anime_poster = main_url + '/posters/11567.34575557493.jpg'

			AddFolder(anime_names[i].text.encode('utf-8').replace('смотреть онлайн', ''), 'anime_title', icon = anime_poster, anime_page_url = anime_urls[i], info = anime_plots[i].text.encode('utf-8'))

	xbmcplugin.endOfDirectory(addon_handle)

def AnimeOngoing():
	ongoing_result = Session.get(main_url + '/ongoing?view=big-list')
	anime_information = BS(ongoing_result.content, 'html.parser')

	anime_names = anime_information.find_all('h2', class_ = 'line-1')
	anime_posters = anime_information.find_all('img')
	anime_plots = anime_information.find_all('div', class_ = 'm-catalog-item__description')
	anime_urls = AnimeUrlFixer(anime_information.find_all('a', rel = 'nofollow'))

	for i in range(len(anime_names)):
		anime_poster = main_url + anime_posters[i].attrs['src']

		if Session.get(anime_poster).status_code == 404:
			anime_poster = main_url + '/posters/11567.34575557493.jpg'

		AddFolder(anime_names[i].text.encode('utf-8').replace('смотреть онлайн', ''), 'anime_title', icon = anime_poster, anime_page_url = anime_urls[i], info = anime_plots[i].text.encode('utf-8'))

	xbmcplugin.endOfDirectory(addon_handle)

def MyList():
	AddFolder('Смотрю', 'type_list', ltype = 'watching')
	AddFolder('Просмотрено', 'type_list', ltype = 'completed')
	AddFolder('Отложено', 'type_list', ltype = 'onhold')
	AddFolder('Брошено', 'type_list', ltype = 'dropped')
	AddFolder('Запланировано', 'type_list', ltype = 'planned')
	xbmcplugin.endOfDirectory(addon_handle)

def GenerateMyList(list_type):
	ongoing_result = Session.get(main_url + '/users/{0}/list/{1}'.format(AccID, list_type))
	anime_information = BS(ongoing_result.content, 'html.parser')

	anime_data = anime_information.find_all('tr', class_ = 'm-animelist-item')

	for data in anime_data:
		info = data.find('a')
		AddFolder(re.split(r'\W/ ', info.text)[0].encode('utf-8'), 'anime_title', anime_page_url = info.attrs['href'])

	xbmcplugin.endOfDirectory(addon_handle)

def MainMenu():
	AddFolder('Поиск', 'anime_search', icon = 'https://imageup.ru/img66/3615282/search.png')
	AddFolder('Онгоинги', 'anime_ongoing', icon = 'https://imageup.ru/img260/3660525/ongoing.jpg')
	AddFolder('Мой список', 'my_list')
	xbmcplugin.endOfDirectory(addon_handle)

def router(paramstring):
	params = dict(urlparse.parse_qsl(paramstring))

	try:
		if params:
			if params['action'] == 'anime_search':
				AnimeSearch()

			elif params['action'] == 'anime_ongoing':
				AnimeOngoing()

			elif params['action'] == 'my_list':
				MyList()

			elif params['action'] == 'type_list':
				GenerateMyList(params['ltype'])

			elif params['action'] == 'anime_title':
				GenerateEpisodeList(params['anime_page_url'])

			elif params['action'] == 'anime_episode':
				GenerateLocalTeamList(params['episode_page_url'])

			elif params['action'] == 'video_episode':
				PlayVideo(params['label'], params['url'], params['sub'])

			else:
				Message('Invalid paramstring!', str(paramstring))
				xbmc.log(msg='Invalid paramstring: ' + str(paramstring), level=xbmc.LOGDEBUG);
		else:
			MainMenu()
	except Exception as e:
		Message('Paramstring error!', str(e))

if __name__ == '__main__':
	router(sys.argv[2][1:])