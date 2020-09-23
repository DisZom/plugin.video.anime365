# -*- coding: utf-8 -*-
import sys, json
import requests, certifi
import urllib3, urllib, urlparse
from bs4 import BeautifulSoup as BS
import xbmc, xbmcgui, xbmcaddon, xbmcplugin

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])

main_url = 'https://smotret-anime.online'
urllib_https = urllib3.PoolManager(ca_certs=certifi.where())

xbmcplugin.setContent(addon_handle, 'videos')

my_addon = xbmcaddon.Addon('plugin.video.anime365')

acc_login = my_addon.getSetting('sa-login')
acc_paswd = my_addon.getSetting('sa-paswd')

local_type = '/ozvuchka'

def BuildUrlDirection(**kwargs):
	return "{0}?{1}".format(base_url, urllib.urlencode(kwargs))

def Message(title, message):
	xbmcgui.Dialog().ok(title, message)

def AddDirectionFolder(label, action, **kwargs):
	if 'icon' not in kwargs:
		kwargs.setdefault('icon', "DefaultFolder.png")

	if 'info' not in kwargs:
		kwargs.setdefault('info', "")

	item = xbmcgui.ListItem(label)
	item_url = BuildUrlDirection(label = label, action = action, **kwargs)
	
	item.setArt({'poster': kwargs['icon'], 'banner': kwargs['icon'], 'icon': kwargs['icon']})

	item.setInfo('video', {'title': label, 'plot': kwargs['info']})

	xbmcplugin.addDirectoryItem(handle=addon_handle, url=item_url, listitem=item, isFolder=True)

def play_video(video_name, video_url):
	Item = xbmcgui.ListItem(video_name, path=video_url)
	Item.setProperty('IsPlayable', 'true')
	xbmc.Player().play(item=video_url, listitem=Item)

def GetAccountSession():
	header = {
		u'User-Agent': u'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 YaBrowser/20.8.3.115 Yowser/2.5 Safari/537.36'
	}

	reSes = requests.Session()

	reSes.headers.update(header)

	login_url = main_url + '/users/login'

	csrf = BS(reSes.get(login_url).content,'html.parser').find('input',  type = 'hidden').get_attribute_list('value')[0]

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

Session = GetAccountSession()

def AnimeUrlFixer(bad_urls):
	fix_urls = []

	for i in range(len(bad_urls)-1):
		if bad_urls[i].get_attribute_list('href')[0] != bad_urls[i+1].get_attribute_list('href')[0]:
			fix_urls.append(bad_urls[i].get_attribute_list('href')[0])

	return fix_urls

def ExtractVideoURL(anime_page_url):
	page_info = Session.get(main_url + anime_page_url)

	translation_url =  str(BS(page_info.content, 'html.parser').find('iframe', id = "videoFrame").attrs['src'])

	translation_result = Session.get(translation_url)

	translation_video_element = BS(translation_result.content, 'html.parser').find("video")

	try:
		if translation_video_element == None:
			video_data = [{"urls":[str(main_url + "/posters/11567.34575557493.jpg")]}]
		else:
			video_data = json.loads(str(translation_video_element.attrs["data-sources"]))

	except Exception as e:
		Message("Extract", str(e))

	return video_data[0]["urls"][0]

def AnimeSearch():
	kb = xbmc.Keyboard()
	kb.setDefault('')
	kb.setHeading('Поиск')
	kb.doModal()

	if kb.isConfirmed():
		query = kb.getText()

		search_result = Session.get(main_url + '/catalog/search?page=1&q=' + str(query))

		try:
			anime_information = BS(search_result.content,'html.parser')

			anime_names = anime_information.find_all('h2', class_ = "line-1")
			anime_posters = anime_information.find_all('img')
			anime_plots = anime_information.find_all('div', class_ = "m-catalog-item__description")
			anime_urls = AnimeUrlFixer(anime_information.find_all('a', rel="nofollow"))
		except Exception as e:
			Message('ParserError', str(e))

		for i in range(len(anime_names)):
			try:
				anime_name = str(anime_names[i].text.encode('utf-8').replace('смотреть онлайн', ''))
				anime_poster = str(main_url + anime_posters[i].get_attribute_list('src')[0])
				anime_plot = str(anime_plots[i].text.encode('utf-8'))
				anime_url = str(anime_urls[i])
			except Exception as e:
				Message('AnimeInfoError', str(e))

			try:
				check_for_poster = str(Session.get(anime_poster).status_code)

				if check_for_poster == '404':
					anime_poster = str(main_url + '/posters/11567.34575557493.jpg')

			except Exception as e:
				Message('Poster Error', str(e))

			try:
				AddDirectionFolder(anime_name, 'anime_title', icon = anime_poster, anime_page_url = anime_url, info = anime_plot)
			except Exception as e:
				Message('AddDirError', str(e))

	xbmcplugin.endOfDirectory(addon_handle)

def GenerateEpisodeList(page_url):
	episodes_result = Session.get(main_url + page_url)

	episodes_info = BS(episodes_result.content,'html.parser')
	eps_names_with_urls = episodes_info.find_all('div', class_="col s12 m6 l4 x3")

	episodes_names = []
	episodes_urls = []

	for i in range(len(eps_names_with_urls)):
		try:
			episodes_names.append(eps_names_with_urls[i].find('a').text.replace('play_circle_filled','').encode('utf-8'))
		except Exception as e:
			Message("Episode Append Name", str(e))
		try:
			episodes_urls.append(str(eps_names_with_urls[i].find("a").get_attribute_list('href')[0]) + local_type)
		except Exception as e:
			Message("Episode Append Url", str(e))

	try:
		for i in range(len(episodes_names)):
			AddDirectionFolder(episodes_names[i], 'anime_episode', page_video_url = episodes_urls[i])
	except Exception as e:
		Message("Episode Error", str(e))

	xbmcplugin.endOfDirectory(addon_handle)

def GenerateLocalTeamList(episode_url):
	localteam_result = urllib_https.request('GET', main_url + episode_url).data.decode('utf-8')

	local_name = []
	local_url = []

	team_table = BS(localteam_result, "html.parser").find_all('div', class_ = "row")[2].find_all('a')

	for i in range(len(team_table)):
		local_name.append(team_table[i].text)
		local_url.append(team_table[i].attrs["href"])
	for i in range(len(local_name)):
		AddDirectionFolder(local_name[i].encode("utf-8"), 'video_episode', video_url = ExtractVideoURL(local_url[i]))

	xbmcplugin.endOfDirectory(addon_handle)

def MainMenu():
	AddDirectionFolder('Поиск','anime_search', icon = 'https://imageup.ru/img66/3615282/search.png', info = "Search")
	xbmcplugin.endOfDirectory(addon_handle)

def router(paramstring):
	params = dict(urlparse.parse_qsl(paramstring))

	try:
		if params:
			if params['action'] == 'anime_search':
				AnimeSearch()
			elif params['action'] == 'anime_title':
				GenerateEpisodeList(params["anime_page_url"])
			elif params['action'] == 'anime_episode':
				GenerateLocalTeamList(params["page_video_url"])
			elif params['action'] == 'video_episode':
				play_video(params['label'], params['video_url'])
			else:
				Message('Invalid paramstring!',str(paramstring))
		else:
			MainMenu()
	except Exception as e:
		Message('ParamsError', str(e))

if __name__ == '__main__':
	router(sys.argv[2][1:])
