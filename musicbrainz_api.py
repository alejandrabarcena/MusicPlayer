import requests
import json
import time
from typing import Dict, List, Optional

class MusicBrainzAPI:
    """
    MusicBrainz API client for searching classical music information
    """
    
    def __init__(self):
        self.base_url = "https://musicbrainz.org/ws/2/"
        self.user_agent = "PythonMusicPlayer/1.0 (Classical Music Search)"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed 1 request per second as per MusicBrainz rules"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make a request to MusicBrainz API with rate limiting"""
        try:
            self._rate_limit()
            params['fmt'] = 'json'
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"MusicBrainz API error: {e}")
            return None
    
    def search_artist(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for classical composers and performers"""
        params = {
            'query': f'{query} AND type:person',
            'limit': limit
        }
        
        data = self._make_request('artist', params)
        if data and 'artists' in data:
            results = []
            for artist in data['artists']:
                # Filter for classical music artists
                artist_info = {
                    'id': artist.get('id'),
                    'name': artist.get('name'),
                    'sort_name': artist.get('sort-name'),
                    'country': artist.get('country'),
                    'begin_area': artist.get('begin-area', {}).get('name') if artist.get('begin-area') else None,
                    'life_span': self._format_life_span(artist.get('life-span')),
                    'score': artist.get('score', 0)
                }
                results.append(artist_info)
            return sorted(results, key=lambda x: x['score'], reverse=True)
        return []
    
    def search_work(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for classical works (compositions)"""
        params = {
            'query': query,
            'limit': limit
        }
        
        data = self._make_request('work', params)
        if data and 'works' in data:
            results = []
            for work in data['works']:
                work_info = {
                    'id': work.get('id'),
                    'title': work.get('title'),
                    'type': work.get('type'),
                    'language': work.get('language'),
                    'composer': self._extract_composer(work.get('artist-relation')),
                    'score': work.get('score', 0)
                }
                results.append(work_info)
            return sorted(results, key=lambda x: x['score'], reverse=True)
        return []
    
    def search_recording(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for classical music recordings"""
        params = {
            'query': query,
            'limit': limit
        }
        
        data = self._make_request('recording', params)
        if data and 'recordings' in data:
            results = []
            for recording in data['recordings']:
                recording_info = {
                    'id': recording.get('id'),
                    'title': recording.get('title'),
                    'length': recording.get('length'),
                    'artist_credit': self._format_artist_credit(recording.get('artist-credit')),
                    'releases': self._extract_releases(recording.get('releases', [])),
                    'score': recording.get('score', 0)
                }
                results.append(recording_info)
            return sorted(results, key=lambda x: x['score'], reverse=True)
        return []
    
    def get_classical_composers(self) -> List[Dict]:
        """Get famous classical composers"""
        famous_composers = [
            "Johann Sebastian Bach", "Wolfgang Amadeus Mozart", "Ludwig van Beethoven",
            "Frédéric Chopin", "Franz Schubert", "Robert Schumann", "Franz Liszt",
            "Johannes Brahms", "Pyotr Ilyich Tchaikovsky", "Sergei Rachmaninoff",
            "Claude Debussy", "Igor Stravinsky", "Antonio Vivaldi", "George Frideric Handel",
            "Joseph Haydn", "Franz Joseph Haydn", "Dmitri Shostakovich"
        ]
        
        all_composers = []
        for composer in famous_composers[:5]:  # Limit to avoid too many API calls
            results = self.search_artist(composer, limit=1)
            if results:
                all_composers.extend(results)
            
        return all_composers
    
    def _format_life_span(self, life_span: Optional[Dict]) -> str:
        """Format birth and death dates"""
        if not life_span:
            return ""
        
        begin = life_span.get('begin', '')
        end = life_span.get('end', '')
        
        if begin and end:
            return f"({begin} - {end})"
        elif begin:
            return f"(b. {begin})"
        elif end:
            return f"(d. {end})"
        return ""
    
    def _format_artist_credit(self, artist_credit: Optional[List]) -> str:
        """Format artist credit names"""
        if not artist_credit:
            return ""
        
        names = []
        for credit in artist_credit:
            if isinstance(credit, dict) and 'artist' in credit:
                names.append(credit['artist']['name'])
            elif isinstance(credit, str):
                names.append(credit)
        
        return ", ".join(names)
    
    def _extract_composer(self, relations: Optional[List]) -> str:
        """Extract composer from work relations"""
        if not relations:
            return ""
        
        for relation in relations:
            if relation.get('type') == 'composer' and 'artist' in relation:
                return relation['artist']['name']
        return ""
    
    def _extract_releases(self, releases: List) -> List[str]:
        """Extract release titles from recordings"""
        if not releases:
            return []
        
        release_titles = []
        for release in releases[:3]:  # Limit to first 3 releases
            title = release.get('title', '')
            if title:
                release_titles.append(title)
        
        return release_titles
    
    def search_classical_by_period(self, period: str) -> List[Dict]:
        """Search for classical music by historical period"""
        period_queries = {
            'baroque': 'Bach OR Vivaldi OR Handel OR Telemann OR Purcell',
            'classical': 'Mozart OR Haydn OR Clementi OR Boccherini',
            'romantic': 'Beethoven OR Chopin OR Schubert OR Schumann OR Brahms OR Liszt',
            'modern': 'Stravinsky OR Debussy OR Ravel OR Bartók OR Prokofiev'
        }
        
        query = period_queries.get(period.lower(), period)
        return self.search_artist(query, limit=10)