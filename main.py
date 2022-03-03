# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcaddon, xbmcplugin
import urllib, urlparse
import sys

try:
	import simplejson as json
except ImportError:
	import json

from anime365 import PyAnime365

BaseURL = sys.argv[0]
AddonHandle = int(sys.argv[1])
Addon = xbmcaddon.Addon("plugin.video.anime365")

xbmcplugin.setContent(AddonHandle, "videos")

Anime365 = PyAnime365(Addon.getSetting("sa-login"), Addon.getSetting("sa-paswd"), "sub" if Addon.getSetting("local-type") == "Subtitles" else "voice")

def BuildURLDirection(**kwargs):
	return "{0}?{1}".format(BaseURL, urllib.urlencode(kwargs))

def Message(title, message):
	xbmcgui.Dialog().ok(title, message)

def AddFolder(label, action, **kwargs):
	Item = xbmcgui.ListItem(label)
	ItemURL = BuildURLDirection(label = label, action = action, **kwargs)

	if "icon" in kwargs:
		Item.setArt({"poster": kwargs["icon"], "banner": kwargs["icon"], "icon": kwargs["icon"]})

	if "info" in kwargs:
		Anime = kwargs["info"]

		Item.setArt({"poster": Anime["poster"], "banner": Anime["poster"], "icon": Anime["poster"]})
		Item.setInfo("video", {"title": label, "plot": Anime["description"]})

	xbmcplugin.addDirectoryItem(handle = AddonHandle, url = ItemURL, listitem = Item, isFolder = True)

def PlayVideo(videoTitle, videoPath, subPath):
	Item = xbmcgui.ListItem(videoTitle, path = videoPath)
	Item.setProperty("IsPlayable", "true")

	if subPath:
		Item.setSubtitles([subPath])
		xbmc.Player().showSubtitles(True)

	xbmc.Player().play(item = videoPath, listitem = Item)

def AnimeSearch():
	kb = xbmc.Keyboard()
	kb.setDefault("")
	kb.setHeading("Поиск")
	kb.doModal()

	if kb.isConfirmed():
		AnimeList = Anime365.GetAnimeListByQuery(kb.getText())

		for Anime in AnimeList:
			AddFolder(Anime["russian"].encode("utf-8"), "anime_title", info = Anime)

	xbmcplugin.endOfDirectory(AddonHandle)

def LocalTeamList(animeID):
	TranslationList = Anime365.GetTranslationListByID(animeID)

	for Translation in TranslationList:
		if len(Translation["translation"]) == 1:
			AddFolder(Translation["author"].encode("utf-8"), "anime_episode", playerData = Anime365.ExtractVideoData(Translation["translation"][0]["episodeURL"]))
			continue

		AddFolder(Translation["author"].encode("utf-8"), "anime_transaltion", episodes = Translation["translation"])

	xbmcplugin.endOfDirectory(AddonHandle)

def EpisodeList(episodes):
	for Episode in episodes:
		AddFolder("Серия {0}".format(Episode["episode"]), "anime_episode", playerData = Anime365.ExtractVideoData(Episode["episodeURL"]))

	xbmcplugin.endOfDirectory(AddonHandle)

def MyList():
	AddFolder("Смотрю", "user_list", list_type = "watching")
	AddFolder("Просмотрено", "user_list", list_type = "completed")
	AddFolder("Отложено", "user_list", list_type = "onhold")
	AddFolder("Брошено", "user_list", list_type = "dropped")
	AddFolder("Запланировано", "user_list", list_type = "planned")
	xbmcplugin.endOfDirectory(AddonHandle)

def UserList(listType):
	UserAnimeList = Anime365.GetUserList()

	for AnimeID in UserAnimeList[listType]:
		Anime = Anime365.GetAnimeByID(AnimeID)

		AddFolder(Anime["russian"].encode("utf-8"), "anime_title", info = Anime)

	xbmcplugin.endOfDirectory(AddonHandle)

def	AnimeOngoing():
	OngoingList = Anime365.GetOngoingList()

	for AnimeID in OngoingList:
		Anime = Anime365.GetAnimeByID(AnimeID)

		AddFolder(Anime["russian"].encode("utf-8"), "anime_title", info = Anime)

	xbmcplugin.endOfDirectory(AddonHandle)

def MainMenu():
	AddFolder("Поиск", "anime_search", icon = "https://imageup.ru/img66/3615282/search.png")
	AddFolder("Онгоинги", "anime_ongoing", icon = "https://imageup.ru/img260/3660525/ongoing.jpg")
	AddFolder("Мой список", "my_list")
	xbmcplugin.endOfDirectory(AddonHandle)

def router(paramstring):
	params = dict(urlparse.parse_qsl(paramstring))

	try:
		if params:
			if params["action"] == "anime_search":
				AnimeSearch()

			elif params["action"] == "anime_ongoing":
				AnimeOngoing()

			elif params["action"] == "my_list":
				MyList()

			elif params["action"] == "user_list":
				UserList(params["list_type"])

			elif params["action"] == "anime_title":
				Anime = eval(params["info"])
				LocalTeamList(Anime["id"])

			elif params["action"] == "anime_transaltion":
				Episodes = eval(params["episodes"])
				EpisodeList(Episodes)

			elif params["action"] == "anime_episode":
				PlayerData = eval(params["playerData"])
				PlayVideo(params["label"], PlayerData["video"], PlayerData["sub"])

			else:
				xbmc.log("Invalid Paramstring: " + str(paramstring), xbmc.LOGDEBUG)
				Message("Invalid Paramstring!", str(paramstring))
		else:
			MainMenu()
	except Exception as e:
		xbmc.log("Paramstring Error: " + str(e), xbmc.LOGDEBUG)
		Message("Paramstring Error!", str(e))

if __name__ == "__main__":
	router(sys.argv[2][1:])