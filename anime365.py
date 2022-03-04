# -*- coding: utf-8 -*-
import re

try:
	import simplejson as json
except ImportError:
	import json

import requests
from bs4 import BeautifulSoup as BSoup

class PyAnime365():
	def __init__(self, login, password, localType = "voice"):
		self.MainURL = "https://smotret-anime.com"
		self.LocalType = localType + "Ru"

		self.LoginHeader = {
			u"User-Agent": u"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.174 YaBrowser/22.1.3.848 Yowser/2.5 Safari/537.36"
		}
		
		self.SessionStatus = False
		self.Session = self.createAccountSession(login, password)

	def createAccountSession(self, login, password):
		LoginURL = self.MainURL + "/users/login"

		LoginSession = requests.Session()
		LoginSession.headers.update(self.LoginHeader)

		CSRFResponse = LoginSession.get(LoginURL)
		CSRF = BSoup(CSRFResponse.content, "html5lib").find("input", type = "hidden").attrs["value"]

		LoginPayloadData = {
			"csrf": CSRF,
			"LoginForm[username]": login,
			"LoginForm[password]": password,
			"yt0": "",
			"dynpage": 1
		}
	
		LoginCheckResponse = LoginSession.post(LoginURL, data = LoginPayloadData)
		LoginCheckText = BSoup(LoginCheckResponse.content, "html5lib").find("li").text

		if "E-mail" in LoginCheckText:
			LoginSession.close()
			self.SessionStatus = False
			print("Invalid E-Mail or password")
			return requests
		else:
			self.SessionStatus = True
			return LoginSession

	def GetAccountID(self):
		MainPageResponse = self.Session.get(self.MainURL)
		MainPageHTML = BSoup(MainPageResponse.content, "html5lib")

		RegexID = re.search(r"users/([0-9]+)/list", str(MainPageHTML.select("#top-dropdown2 > li:nth-child(2) > a[href]")[0]))

		return RegexID.group(1)

	def ExtractVideoData(self, episodeURL):
		VideoElement = BSoup(self.Session.get(episodeURL).content, "html5lib").find("video", {"id": "main-video"})

		if not VideoElement:
			return {}

		VideoURL = json.loads(VideoElement.attrs["data-sources"])[0]["urls"][0]
		SubURL = (self.MainURL + VideoElement.attrs["data-subtitles"].replace("?willcache", "")) if self.LocalType == "subRu" else ""

		return {"video": VideoURL, "sub": SubURL}

	def GetAnimeByID(self, animeID):
		AnimeResponse = self.Session.get(self.MainURL + "/api/series?id={0}".format(animeID))
		AnimeJSON = json.loads(AnimeResponse.content)
		
		if "error" in AnimeJSON:
			return {}
		
		Anime = AnimeJSON["data"]
		
		AnimeTitle = {
			"id": animeID,
			"name": Anime["titles"]["romaji"],
			"russian": Anime["titles"]["ru"] if "ru" in Anime["titles"] else Anime["titles"]["romaji"],
			"poster": Anime["posterUrl"],
			"description": Anime["descriptions"][0]["value"] if "descriptions" in Anime else "Description Is Invalid"
		}

		return AnimeTitle
		
	def GetAnimeListByQuery(self, query):
		AnimeSearchResponse = self.Session.get(self.MainURL + "/api/series?query={0}".format(query))
		AnimeSearchJSON = json.loads(AnimeSearchResponse.content)["data"]

		if not AnimeSearchJSON:
			return []

		AnimeList = []

		for Anime in AnimeSearchJSON:
			AnimeTitle = {
				"id": Anime["id"],
				"name": Anime["titles"]["romaji"],
				"russian": Anime["titles"]["ru"] if "ru" in Anime["titles"] else Anime["titles"]["romaji"],
				"poster": Anime["posterUrl"],
				"description": Anime["descriptions"][0]["value"] if "descriptions" in Anime else "Description Is Invalid"
			}

			AnimeList.append(AnimeTitle)

		return AnimeList

	def GetTranslationListByID(self, animeID):
		AnimeTranslationsResponse = self.Session.get(self.MainURL + "/api/translations?seriesId={0}&type={1}".format(animeID, self.LocalType))
		AnimeTranslationsJSON = json.loads(AnimeTranslationsResponse.content)["data"]

		if not AnimeTranslationsJSON:
			return []

		AnimeTranslationsJSON = sorted(AnimeTranslationsJSON, key = lambda x: x["authorsSummary"])
		AnimeTranslationList = []

		AuthorsTranslation = {}
		CountEpisodes = int(AnimeTranslationsJSON[0]["series"]["numberOfEpisodes"])

		for Translation in AnimeTranslationsJSON:
			if not Translation["authorsSummary"]:
				continue

			if Translation["authorsSummary"] not in AuthorsTranslation:
				AuthorsTranslation[Translation["authorsSummary"]] = []

			AuthorTranslation = {
				"episode": Translation["episode"]["episodeInt"],
				"episodeURL": Translation["embedUrl"]
			}

			AuthorsTranslation[Translation["authorsSummary"]].append(AuthorTranslation)

		for Translation in AuthorsTranslation.items():
			if len(Translation[1]) >= round(CountEpisodes / 2):
				AnimeTranslation = {
					"author": Translation[0],
					"translation": sorted(Translation[1], key = lambda x: int(x["episode"]))
				}

				AnimeTranslationList.append(AnimeTranslation)

		return sorted(AnimeTranslationList, key = lambda x: len(x["translation"]), reverse = True)

	def GetUserList(self):
		AccID = self.GetAccountID()

		UserList = {
			"watching": [], 
			"completed": [],
			"onhold": [],
			"dropped": [],
			"planned": []
		}

		for ListType in UserList.keys():
			UserListResponse = self.Session.get(self.MainURL + "/users/{0}/list/{1}".format(AccID, ListType))
			UserListHTML = BSoup(UserListResponse.content, "html5lib")
			AnimeList = UserListHTML.find_all("tr", class_ = "m-animelist-item")

			for Anime in AnimeList:
				UserList[ListType].append(Anime.attrs["data-id"])

		return UserList

	def GetOngoingList(self):
		OngoingResponse = self.Session.get(self.MainURL + "/ongoing?view=big-list")
		OngoingHTML = BSoup(OngoingResponse.content, "html5lib")

		Animes = OngoingHTML.find_all("h2", class_ = "line-1")
		AnimeList = []

		for Anime in Animes:
			AnimeID = Anime.find("a").attrs["href"].split("-")[-1]
			AnimeList.append(AnimeID)

		return AnimeList

	def GetRandomAnimeList(self):
		RandomAnimesResponse = self.Session.get(self.MainURL + "/random?view=big-list")
		RandomAnimesHTML = BSoup(RandomAnimesResponse.content, "html5lib")

		Animes = RandomAnimesHTML.find_all("h2", class_ = "line-1")
		AnimeList = []

		for Anime in Animes:
			AnimeID = Anime.find("a").attrs["href"].split("-")[-1]
			AnimeList.append(AnimeID)

		return AnimeList