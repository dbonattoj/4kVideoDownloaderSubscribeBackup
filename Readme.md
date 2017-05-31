# 4k video downloader playlist (m3u) maker from subscription

**Warning:** This is a really bad coded project as I did not had the time and needed this asap.

## Problem definition

When you use 4k video downloader for downloading a playlist, it works very well and make you a playlist file (m4u). However, if the author of the playlist add a new video, you are stuck and have to manually download this video and add it to the right folder and to the right playlist.



An alternative is to subscribe to the channel. This will download all videos of the channel and download new ones all the time. but this will put everything in the same folder, and don't let you the possibility to have playlist generated. Thus, you don't know the ordering of the videos, which are news, if there are videos that are out of the playlist, etc..



## Solution

The idea is to subscribe only to the channels and use those two scripts:

### getLastsTitles.py:

This script throws you back a list of the last 5 days of downloaded videos.

you can send it a minimal date like this ./getLastsTitles.py year month day

### ytPlaylists.py:

This is the main script.

You must setup your 4kvideodownloader database path.

After that, it will scrap youtube by using the subscriptions in the database and make playlists using your videos in the folders.

If there are videos in the folder that are not put in a playlist, it will create a NOT_CLASSIFIED.m3u playlist

**Warning:** There are sometime bugs with the filesnames and they are put into the NOT_CLASSIFIED playlist.

By default, the software will save the current date in the name of the playlist.

**Warning:** If you remove a video file, it will not appear in the created playlist!



## Caution

Use those scripts at your own risks. However, they don't modify the database nor the downloaded files ;)