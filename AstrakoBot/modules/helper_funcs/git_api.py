import urllib.request as url
import json
import datetime

VERSION = "0.1.4"
APIURL = "http://api.github.com/repos/"

def vercheck() -> str:
    return str(VERSION)

#Repo-wise stuff

def getData(repoURL):
    try:
        with url.urlopen(APIURL + repoURL + "/releases") as data_raw:
            repoData = json.loads(data_raw.read().decode())
            return repoData
    except:
        return None

def getLastestReleaseData(repoData):
    return repoData[0]

#Release-wise stuff

def getAuthor(releaseData):
    return releaseData['author']['login']
    
def getAuthorUrl(releaseData):
    return releaseData['author']['html_url']
    
def getReleaseName(releaseData):
    return releaseData['name']

def getReleaseDate(releaseData):
    return releaseData['published_at']

def getAssetsSize(releaseData):
    return len(releaseData['assets'])
  
def getAssets(releaseData):
    return releaseData['assets']
    
def getBody(releaseData): #changelog stuff
    return releaseData['body']

#Asset-wise stuff

def getReleaseFileName(asset): 
    return asset['name']

def getReleaseFileURL(asset):
    return asset['browser_download_url']

def getDownloadCount(asset):
    return asset['download_count']

def getSize(asset):
    return asset['size']
