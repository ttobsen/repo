# -*- coding: utf-8 -*-
import requests
import time
import datetime
import gui
import xbmcgui,xbmcplugin,sys

RAN_API_BASE = 'https://middleware.7tv.de'

def get_playlist_url(m3u8_url, height=720):
    import re
    try:
        print("get_playlist_url "+m3u8_url)
        response = requests.get(m3u8_url)
        m3u8 = response.read()
        stream_url_prefix = m3u8_url[:m3u8_url.rfind('/') + 1]
        pattern = 'BANDWIDTH=(\d+).*?RESOLUTION=\d+x(\d+).*?\n(.+?)\n'
        videos = re.findall(pattern, m3u8)
        videos = sorted(videos, key=lambda k: (k[1], k[0]))
        del videos[0]
        stream_url_suffix = videos[0][2].replace('\r', '')
        for bandwidth, _height, suffix in videos:
            if int(_height) > height:
                break
            stream_url_suffix = suffix.replace('\r', '')
        stream_url = stream_url_prefix + stream_url_suffix
        if stream_url.startswith('http') and '.m3u8' in stream_url:
            return stream_url
        return m3u8_url
    except:
        return m3u8_url


def list_videos(resource, reliveOnly):
    try:
        json_url = RAN_API_BASE + resource
        print ("###########"+json_url)
        response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})
        videos = response.json()['contents']
    except:
        return gui.end_listing()
    try:
        is_livestream = videos[0]['type'] == 'livestream'
    except (KeyError, IndexError):
        is_livestream = False
    if is_livestream:
        videos = sorted(videos, key=lambda k: k.get('streamdate_start'))
        timestamp_now = time.time()
    for video in videos:
        if is_livestream:
            stream_date_end = video['streamdate_end']
            if stream_date_end >= timestamp_now:
                stream_date_start = video['streamdate_start']
                if stream_date_start <= timestamp_now:
                    duration_in_seconds = stream_date_end - timestamp_now
                    playable = True
                    print("YYY: "+video["resource"])
                    title = '[B][COLOR red]%s[/COLOR][/B]' % video['teaser']['title']
                    year = datetime.datetime.now().year
                else:
                    date = datetime.datetime.fromtimestamp(stream_date_start)
                    year = date.year
                    date = date.strftime('%d.%m.%Y, %H:%M')
                    duration_in_seconds = stream_date_end - stream_date_start
                    playable = False
                    title = video['teaser']['title']
                    title = '[COLOR blue]%s[/COLOR] %s' % (date, video['teaser']['title'])
            else:
                continue
        else:
            duration_in_seconds = video['duration_in_seconds']
            date = datetime.datetime.fromtimestamp(video['published'])
            year = date.year
            date = date.strftime('%d.%m.%Y')
            playable = True
            title = '[COLOR blue]%s[/COLOR] %s' % (date, video['teaser']['title'])
        resource = video['resource']
        thumb = video['teaser']['image']  # .replace('ran_app_1280x720', 'ran_app_512x288')
        desc = video['teaser']['image_alt'] or video['teaser']['title']

        if 'False' in reliveOnly or 'Relive' in video['teaser']['title'] or 'Re-Live' in video['teaser']['title']:
            gui.add_video(title, thumb, {'f': 'play', 'resource': resource},
                      {'Title': video['teaser']['title'], 'Plot': desc, 'Genre': 'Sport', 'Year': year},
                      duration_in_seconds, thumb, is_playable=playable)
    gui.make_info_view_possible()
    gui.info_view()
    gui.end_listing()


def get_number_livestreams():
	print("get_number_livestreams")
	try:
		json_url = RAN_API_BASE + '/ran-mega/mobile/v1/livestreams.json'
		response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})
		videos = response.json()['contents']
		timestamp_now = time.time()
		number_livestreams = 0
		for video in videos:
			stream_date_end = video['streamdate_end']
			if stream_date_end >= timestamp_now:
				stream_date_start = video['streamdate_start']
				if stream_date_start <= timestamp_now:
					number_livestreams += 1
		return number_livestreams
	except:
		return 0


def _get_videos(video_id, access_token, client_name, client_location, salt, source_id=None):
    from hashlib import sha1
    print("-XYZ----")
    ## Step 1
    if source_id is None:
        json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s?' \
                   'access_token=%s&client_location=%s&client_name=%s' \
                   % (video_id, access_token, client_location, client_name)
        response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})
        source_id = response.json()['sources'][0]['id']
    ## Step 2
    client_id_1 = salt[:2] + sha1(
        ''.join([str(video_id), salt, access_token, client_location, salt, client_name]).encode('utf-8')).hexdigest()
    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources?' \
               'access_token=%s&client_location=%s&client_name=%s&client_id=%s' \
               % (video_id, access_token, client_location, client_name, client_id_1)
    response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})
    server_id = response.json()['server_id']
    ## Step 3
    client_id_2 = salt[:2] + sha1(
        ''.join([salt, str(video_id), access_token, server_id, client_location, str(source_id), salt,
                 client_name]).encode('utf-8')).hexdigest()
    json_url = 'http://vas.sim-technik.de/vas/live/v2/videos/%s/sources/url?' \
               'access_token=%s&client_location=%s&client_name=%s&' \
               'client_id=%s&server_id=%s&source_ids=%s' \
               % (video_id, access_token, client_location, client_name, client_id_2, server_id, source_id)
    response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})        
    videos = response.json()['sources']
    return sorted(videos, key=lambda k: k.get('bitrate'))


def get_video_url(resource, height):
    from hashlib import sha1
    json_url = RAN_API_BASE + resource    
    response = requests.get(json_url, headers={'Accept-Encoding': 'gzip'})
    json_data = response.json()
    if json_data['type'] == 'livestream':
        url = json_data['stream_url']
        salt = "01iegahthei8yok0Eopai6jah5Qui0qu"
        userAgent = 'User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'
        #https://vas-live-mdp.glomex.com/live/1.0/getprotocols?access_token=ran-app&client_location=http%3A%2F%2Fapp.ran.de%2Fran-ri-event03&client_token=01687d1ae1a5e3022c022b74756dfe7d0082e041c1&property_name=ran-ri-event03
        access_token="ran-app"
        location="http://app.ran.de/"+url
        client_token=salt[:2] + sha1(''.join([url,salt,access_token,location])).hexdigest()
        newurl="https://vas-live-mdp.glomex.com/live/1.0/getprotocols?access_token="+access_token+"&client_location="+location+"&client_token="+client_token+"&property_name="+url 
        print(newurl)        
        response = requests.get(newurl, headers={'Accept-Encoding': 'gzip','user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})
        print(response.json())
        
        servertoken=response.json()["server_token"]

        protokol="dash"        
        client_token=salt[:2] + sha1(''.join([url,salt,access_token,servertoken,location+protokol])).hexdigest()          
        url2="https://vas-live-mdp.glomex.com/live/1.0/geturls?access_token="+access_token+"&client_location="+location+"&client_token="+client_token+"&property_name=" +url+"&protocols=" + protokol+"&server_token=" + servertoken
        response = requests.get(url2, headers={'Accept-Encoding': 'gzip','user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'})
        jsondata=response.json()    
        print(jsondata)        
        print("###############################")        
        urld=jsondata["urls"][protokol]["clear"]["url"]                
        addon_handle = int(sys.argv[1])
        listitem = xbmcgui.ListItem(path=urld+"|"+userAgent)         
        listitem.setProperty("inputstream.adaptive.license_type", "com.widevine.alpha")
        listitem.setProperty("inputstream.adaptive.manifest_type", "mpd")
        listitem.setProperty('inputstreamaddon', "inputstream.adaptive")
        listitem.setProperty("inputstream.adaptive.manifest_update_parameter", "full")
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem)
        return ""
    else:
        video_id = json_data['video_id']
        """
        access_token = 'r''a''n''-''a''p''p'
        client_location = 'h''t''t''p'':''/''/''a''p''p''.''r''a''n''.''d''e''/''%s' % video_id
        client_name = 'r''a''n''-''5''.''7''.''3'
        salt = '0''1''i''e''g''a''h''t''h''e''i''8''y''o''k''0''E''o''p''a''i''6''j''a''h''5''Q''u''i''0''q''u'
        source_id = 6
        access_token = 'p''r''o''s''i''e''b''e''n'
        client_location = json_data['url']
        client_name = 'k''o''l''i''b''r''i''-''2''.''0''.''1''9''-''s''p''l''e''c''4'
        salt = '0''1''!''8''d''8''F''_'')''r''9'']''4''s''[''q''e''u''X''f''P''%'
        source_id = 4
        """
        access_token = 'h''b''b''t''v'
        client_location = json_data['url']
        salt = '0''1''r''e''e''6''e''L''e''i''w''i''u''m''i''e''7''i''e''V''8''p''a''h''g''e''i''T''u''i''3''B'
        # http://hbbtv.prosieben.de/common/js/videocenter.js
        # __PATTERN = 'salt\s*:\s*"01(.+?)"'
        source_id = 4
        videos = _get_videos(video_id, access_token, access_token, client_location, salt, source_id)
        # height = (234, 270, 396, 480, 540, 720)
        url = videos[-1]['url']
        if height < 396:
            import re
            if height == 270:
                return re.sub(r'(.+?)(tp\d+.mp4)(.+)', r'\1tp%02d.mp4\3' % 4, url)
            # height == 234
            return re.sub(r'(.+?)(tp\d+.mp4)(.+)', r'\1tp%02d.mp4\3' % 3, url)
        if height == 396:
            return videos[0]['url']
        # else height in (480, 540, 720)
        # check available qualities:
        if 'tp12.mp4' in url:
            # available video ids are: (12,11,10,09,06) --> (720,720,540,540,360)
            if height == 480:
                return videos[0]['url']  # 360
            if height == 540:
                return videos[2]['url']  # 540
            # else: return highest --> 720
        # else: available video ids are: (08,07,06) --> (432,432,360)
        # highest is 432 and we want 480 or 540 or 720
        # return highest
        return url
