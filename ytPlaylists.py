import sqlite3
from urllib.request import urlopen
import bs4 as BeautifulSoup

import os

from difflib import SequenceMatcher

from datetime import datetime


def sanitize(filename):
    ret = filename
    ret = ret.replace("/", "_")
    ret = ret.replace("\\", "_")
    ret = ret.replace("\n", "_")
    ret = ret.replace("!", "_")
    ret = ret.replace("?", "_")
    ret = ret.replace(":", "_")
    ret = ret.replace("&", "_")
    ret = ret.replace("|", "_")
    ret = ret.replace("[", "_")
    ret = ret.replace("]", "_")

    ret = ret.replace("__", "_")
    ret = ret.replace("_ _", "_")
    ret = ret.replace("__", "_")

    return ret

class FileExplorer(object):
    def __init__(self, folder_path):
        """The folder must contain only the videos"""
        self.folder = folder_path
        self.files = self._setAllFiles(folder_path)

    def _setAllFiles(self, folder_path):
        f = []
        for (dirpath, dirnames, filenames) in os.walk(folder_path):
            filenames = [filename for filename in filenames if "srt" not in filename and "m3u" not in filename]
            f.extend(filenames)
            break
        return f

    def similar(self, str1, str2):
        a = sanitize(str1)
        b = sanitize(str2)
        return SequenceMatcher(None, a, b).ratio()

    def getSimilarityDictionary(self, title_sequence):
        ret = {}
        for (title, url) in title_sequence:
            max_similarity = -1
            out_file = None
            for file in self.files:
                similarity = self.similar(title, file)
                if similarity > max_similarity:
                    max_similarity = similarity
                    out_file = file
            ret[title] = out_file

        return ret

class m3uMaker(object):
    def __init__(self, videos, similarity_dict, folder_path, playlist_name, date=True):
        self.videos = videos
        self.similarity_dict = similarity_dict
        self.folder_path = folder_path
        self.playlist_name = sanitize(playlist_name)
        self.date = ""
        if date:
            d = datetime.today()
            self.date = str(d.year) + str(d.month) + str(d.day)


    def generate(self):
        files_ok = []
        with open(self.folder_path + "/" + self.playlist_name + self.date + ".m3u", 'w', encoding='utf-8') as f:
            for (video_title, video_url) in self.videos:
                try:
                    real_name = self.similarity_dict[video_title]
                except:
                    real_name = video_title
                if real_name:
                    f.write(real_name)
                    f.write("\n")
                    files_ok.append(real_name)

        return files_ok




class FourKVideoDB(object):
    def __init__(self, path):
        self.db = path

    def getAllChainWithPath(self, asDict=True):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            query = """
            SELECT sub.query as chain_url, sub.title as chain_title, subs.path
            FROM subscriptions as sub
            INNER JOIN subscription_settings as subs
            ON subs.subscriptionId = sub.id;
            """
            rows = c.execute(query)

        ret = rows
        if asDict:
            ret = {}
            for row in rows:
                chain_url = row[0]
                chain_title = row[1]
                hdd_path = row[2]
                ret[chain_title] = (
                    self.chainToPlaylist(chain_url),
                    hdd_path
                )

        return ret

    def getChains(self, asDict=True):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            query = "SELECT id, query, title, lastReferenceStr, lastTimestamp FROM subscriptions;"
            rows = c.execute(query)

        ret = rows
        if asDict:
            ret = {}
            for row in rows:
                id = row[0]
                query = row[1]
                title = row[2]
                lastReferenceStr = row[3]
                lastTimestamp = row[4]

                ret[title] = {
                    'id': id,
                    'query': self.chainToPlaylist(query),
                    'lastReferenceStr': lastReferenceStr,
                    'lastTimestamp': lastTimestamp,
                }

        return ret

    def getAllPlaylistsUrls(self):
        ret = {}
        chains = self.getChains()
        for key in chains.keys():
            ret[key] = chains[key]['query']

        return ret

    def getVideosLinksBySubscription(self):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            query = "SELECT id, subscriptionId, reference FROM subscription_elements;"
            rows = c.execute(query)
        return rows

    def getSubscriptionVideos(self, asDict=True):
        with sqlite3.connect(self.db) as conn:
            c = conn.cursor()
            query = """
            SELECT reference, title, lastTimestamp, query
            FROM subscription_elements as sube
            INNER JOIN subscriptions as sub
            ON sube.subscriptionId = sub.id
            """
            rows = c.execute(query)

        ret = rows
        if asDict:
            ret = {}
            for row in rows:
                video = row[0]
                chain = row[1]
                lastTimestamp = row[2]
                chain_url = row[3]
                if not chain in ret.keys():
                    ret[chain] = []
                ret[chain].append({
                    'video': video,
                    'chain_url': chain_url,
                    'lastTimestamp': lastTimestamp,
                })

        return ret

    def chainToPlaylist(self, chain_url):
        chain_url = chain_url.replace('/feed', '')
        chain_url = chain_url.replace('/videos', '')
        chain_url = chain_url.replace('/featured', '')

        chain_url += "/playlists"
        chain_url = chain_url.replace("//playlists", "/playlists")
        return chain_url



class YTPlaylist(object):

    def __init__(self, fourK_database_path):
        self.fk = FourKVideoDB(fourK_database_path)

    def run(self):
        chains = self.fk.getAllChainWithPath()
        for chain_title in chains.keys():
            print("Doing: " + chain_title)
            chain_url = chains[chain_title][0]
            folder_path = chains[chain_title][1]
            self.processChain(chain_url, folder_path)


    def processChain(self, chain_url, folder_path):
        playlists = self.getPlaylists(chain_url)
        fe = FileExplorer(folder_path)
        files_in_playlist = self.filesInPlaylistInit(fe.files)
        for playlist in playlists:
            playlist_title = playlist[0]
            playlist_url = playlist[1]
            print("--> " + playlist_title)
            videos = self.getVideosNameOrdered(playlist_url)
            similarity_dict = fe.getSimilarityDictionary(videos)
            m3u = m3uMaker(videos, similarity_dict, folder_path, playlist_title)
            files_ok = m3u.generate()
            for filename in files_ok:
                files_in_playlist[filename] = True

        videos_not_in_playlist = []
        for key in files_in_playlist.keys():
            if not files_in_playlist[key]:
                videos_not_in_playlist.append((key, "garbage"))

        if len(videos_not_in_playlist) > 0:
            m3u = m3uMaker(videos_not_in_playlist, None, folder_path, "NOT_CLASSIFIED")
            m3u.generate()


        return playlists

    def filesInPlaylistInit(self, files):
        ret = {}
        for f in files:
            ret[f] = False

        return ret

    def getVideosNameOrdered(self, playlist_url):
        html = urlopen(playlist_url).read()
        soup = BeautifulSoup.BeautifulSoup(html, "lxml")
        links = soup.find_all('a', attrs={'class':'pl-video-title-link'})
        ret = []
        for link in links:
            ret.append((sanitize(link.string), link['href']))

        return ret

    def getPlaylists(self, chain_url):
        html = urlopen(chain_url).read()
        soup = BeautifulSoup.BeautifulSoup(html, "lxml")
        links = soup.find_all('a', attrs={'class': 'yt-uix-tile-link'})
        ret = []
        for link in links:
            title = link.string
            ret.append((title, "https://www.youtube.com" + link['href']))

        return ret


##browse-items-primary > li:nth-child(3) > div.feed-item-dismissable > div > div > div > div.multirow-shelf.shelf-item.c4-visible-on-hover-container.yt-section-hover-container > ul > li:nth-child(1) > div > div.yt-lockup-dismissable > div.yt-lockup-content > h3 > a
#<a class="yt-uix-sessionlink yt-uix-tile-link  spf-link  yt-ui-ellipsis yt-ui-ellipsis-2" dir="ltr" title="Level 2 Tai Chi Test Review" aria-describedby="description-id-262410" data-sessionlink="ei=vVktWeDxF4br1gK0wZKYCQ&amp;ved=CGcQ2yoYACITCKDEyPTDl9QCFYa1VQodtKAEkyibHA" href="/playlist?list=PLrNPUBAMZb8UccPNV6woSHhV2yCjpM1VN">Level 2 Tai Chi Test Review</a>



if __name__ == "__main__":
    root = "C:/Users/Administrator/AppData/Local/4kdownload.com/4K Video Downloader/4K Video Downloader/"
    db = "database.sqlite"

    ytp = YTPlaylist(root + db)
    ytp.run()



