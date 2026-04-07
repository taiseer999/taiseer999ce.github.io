import re
import json

from kodi_six import xbmc
from slyguy.session import Session
from slyguy import gui, inputstream, log

from .language import _
from .constants import IMDB_API_URL, IMDB_API_HEADERS, IMDB_VIDEO_URL, IMDB_QUALITY_MAP, TrailerItem


# find best from https://gist.github.com/henryjfry/8da2b90aa4a4ef09110625a56b2367c7
class IMDB(object):
    def __init__(self, imdb_id):
        self._session = Session(headers=IMDB_API_HEADERS)
        self._imdb_id = imdb_id

    def get_best(self, season_number=-1):
        log.debug("IMDB: Searching best trailer for id '{}' (Season {})".format(self._imdb_id, season_number))
        videos = self._get_imdb_videos()
        best = find_best_trailer(videos, season_number=season_number)
        if not best:
            log.debug('IMDB: No trailer found :(')
            return

        log.debug("IMDB: Best found: {}".format(best))
        best['videos'] = self._get_video_id(best['id'])
        return best

    def get_latest(self):
        variables = {'id': self._imdb_id}
        query = 'query($id: ID!){title(id:$id){latestTrailer{id}}}'
        payload = {'query': query, 'variables': variables}
        data = self._session.post(IMDB_API_URL, json=payload).json()
        try:
            video_id = data['data']['title']['latestTrailer']['id']
        except KeyError:
            return
        else:
            return {'videos': self._get_video_id(video_id)}

    def _get_video_id(self, video_id):
        log.debug("IMDB: Fetching video manifest for video_id: '{}'".format(video_id))
        url = IMDB_VIDEO_URL.format(video_id)
        page = self._session.get(url).text
        r = re.search(r'application/json">([^<]+)', page)
        if not r:
            return

        data = json.loads(r.group(1))
        details = data.get('props', {}).get('pageProps', {}).get('videoPlaybackData', {}).get('video')
        return {i.get('videoDefinition'): i.get('url') for i in details.get('playbackURLs') if i.get('videoMimeType') in ('M3U8', 'MP4')}

    def _get_imdb_videos(self, locale="en-GB", page_size=100):
        all_videos = []
        after_cursor = None
        sha = 'e65c5b1d7cfedf8728d046ff3a76a323b20702713f5c03c8810dd9b09835d873'
        name = 'TitleVideoGallerySubPage'
        url = 'https://api.graphql.imdb.com/'

        while True:
            variables = {
                "const": self._imdb_id,
                "filter": {
                    "maturityLevel": "INCLUDE_MATURE",
                    "nameConstraints": {},
                    "titleConstraints": {}
                },
                "first": page_size,
                "locale": locale,
                "sort": {
                    "by": "DATE",
                    "order": "DESC"
                }
            }

            if after_cursor:
                variables['after'] = after_cursor
                name = 'TitleVideoGalleryPagination'
                sha = 'e1710d91c7f00600952ca606dd8af0815f7448b173140e01bdbaf79d582b0187'
                url = 'https://caching.graphql.imdb.com/'

            payload = {
                "operationName": name,
                "variables": variables,
                "extensions": {
                    "persistedQuery": {
                        "sha256Hash": sha,
                        "version": 1
                    }
                }
            }

            response = self._session.post(url, json=payload)
            data = response.json()
            video_data = data.get("data", {}).get("title", {}).get("videoStrip", {})
            edges = video_data.get("edges", [])
            videos = [edge.get("node", {}) for edge in edges]
            all_videos.extend(videos)

            page_info = video_data.get("pageInfo", {})
            after_cursor = page_info.get("endCursor",'').strip()
            if len(videos) < page_size or not after_cursor:
                break

        return all_videos


def play_imdb(imdb_id, season_number=-1):
    imdb = IMDB(imdb_id)
    best = imdb.get_best(season_number=season_number)
    if not best:
        gui.notification(_.TRAILER_NOT_FOUND)
        return

    item = TrailerItem()
    if 'DEF_AUTO' in best['videos']:
        item.update(
            path = best['videos']['DEF_AUTO'],
            headers = IMDB_API_HEADERS,
            inputstream = inputstream.HLS(),
        )
    else:
        item.update(
            path = 'special://temp/imdb.m3u8',
            headers = IMDB_API_HEADERS,
            proxy_data = {'custom_quality': True},
        )
        with open(xbmc.translatePath(item.path), 'w') as f:
            f.write('#EXTM3U\n#EXT-X-VERSION:3\n')
            for defintion in best['videos']:
                f.write('\n#EXT-X-STREAM-INF:RESOLUTION={},CODECS=avc\n{}'.format(IMDB_QUALITY_MAP.get(defintion, ''), best['videos'][defintion]))

    return item


def extract_season_number(title):
    match = re.search(r"(?:Season|Series)\s*(\d+)", title, re.IGNORECASE)
    return int(match.group(1)) if match else None


def find_best_trailer(trailer_list, season_number=-1):
    # TODO: if a show with no season - should get earliest trailer to avoid spoilers?
    if not trailer_list:
        return None

    season_number = int(season_number)
    # Sort trailers by runtime (longest first)
    sorted_trailers = sorted(
        trailer_list,
        key=lambda x: x.get('runtime', {}).get('value', 0),
        reverse=True
    )

    # Process trailers and extract metadata
    processed_trailers = []
    available_seasons = []
    has_official = False
    has_theatrical = False
    series_title = None
    theatrical_keywords = ['theatrical', 'full', 'final']
    season_keywords = ['season']

    for trailer in sorted_trailers:
        # Skip non-trailer content
        content_type = trailer.get('contentType', {}).get('id', '')
        if content_type != 'amzn1.imdb.video.contenttype.trailer':
            continue

        # Extract basic trailer info
        trailer_info = {
            'id': trailer.get('id'),
            'title': trailer.get('name', {}).get('value', ''),
            'season': None,
            'official': False,
            'theatrical': False
        }

        # Extract season information
        try:
            series_info = trailer.get('primaryTitle', {}).get('series', {})
            if series_info:
                season_info = series_info.get('displayableEpisodeNumber', {}).get('displayableSeason', {})
                trailer_info['season'] = int(season_info.get('season', 0)) or None

                # Get series title for matching
                if not series_title:
                    series_title_info = series_info.get('series', {}).get('titleText', {})
                    series_title = series_title_info.get('text')
        except (ValueError, TypeError, KeyError):
            pass

        # Try to extract season from title if not found above
        if not trailer_info['season']:
            trailer_info['season'] = extract_season_number(trailer_info['title'])

        # Check for theatrical keywords
        title_lower = trailer_info['title'].lower()
        trailer_info['theatrical'] = any(keyword in title_lower for keyword in theatrical_keywords)
        if trailer_info['theatrical'] and not any(keyword in title_lower for keyword in season_keywords):
            has_theatrical = True

        # Check for official trailer (but not for season-specific trailers)
        trailer_info['official'] = 'official' in title_lower and not trailer_info['season']
        if trailer_info['official']:
            has_official = True

        # Track available seasons
        if trailer_info['season'] and trailer_info['season'] not in available_seasons:
            available_seasons.append(trailer_info['season'])

        processed_trailers.append(trailer_info)

    if not processed_trailers:
        return None

    # Determine target season
    target_season = None
    if season_number >= 0 and available_seasons:
        # TODO: if season is 0 - look for "specials"?
        if season_number in available_seasons:
            target_season = season_number
        else:
            # Find the highest season that's <= requested season
            valid_seasons = [s for s in available_seasons if s <= season_number]
            target_season = max(valid_seasons) if valid_seasons else None

    # Find trailers by priority
    # Priority 1: Season-specific trailer if target season exists
    season_trailer = None
    if target_season:
        for trailer in processed_trailers:
            if trailer['season'] == target_season:
                season_trailer = trailer
                break
    elif not target_season and processed_trailers:
        # No valid season match, use first trailer as fallback
        season_trailer = processed_trailers[0]

    # Priority 2: Theatrical trailer
    theatrical_trailer = None
    if has_theatrical:
        for trailer in processed_trailers:
            if trailer['theatrical']:
                theatrical_trailer = trailer
                break

    # Priority 3: Official trailer (prefer non-teaser)
    official_trailer = None
    if has_official:
        # First try to find official non-teaser
        for trailer in processed_trailers:
            if trailer['official'] and 'teaser' not in trailer['title'].lower():
                official_trailer = trailer
                break

        # If no non-teaser official found, take any official
        if not official_trailer:
            for trailer in processed_trailers:
                if trailer['official']:
                    official_trailer = trailer
                    break

    # Priority 4: Series title match
    title_match_trailer = None
    if series_title:
        for trailer in processed_trailers:
            if trailer['title'] == series_title:
                title_match_trailer = trailer
                break

    # Selection logic based on what we found
    # Prefer seasonal match when season is specified
    if target_season and season_trailer:
        return season_trailer

    # Otherwise use priority order: theatrical > official > title match > any trailer
    if theatrical_trailer:
        return theatrical_trailer
    elif official_trailer:
        return official_trailer
    elif title_match_trailer:
        return title_match_trailer
    else:
        return season_trailer  # Falls back to first trailer if no season match
