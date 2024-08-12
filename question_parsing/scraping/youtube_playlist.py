from dataclasses import dataclass
from typing import Final, List

from googleapiclient.discovery import build


@dataclass
class YoutubeVideo:
    title: str
    url: str


class YoutubeProgress:
    JORDAN_HAS_NO_LIFE_PLAYLIST_ID: Final[str] = "PLjTveVh7FakJOoY6GPZGWHHl4shhDT8iV"

    @staticmethod
    def get_youtube_playlist(client_api_token: str) -> List[YoutubeVideo]:
        youtube = build("youtube", "v3", developerKey=client_api_token)
        playlist_id = "PLjTveVh7FakJOoY6GPZGWHHl4shhDT8iV"
        request = youtube.playlistItems().list(
            part="snippet", maxResults=100, playlistId=playlist_id
        )

        videos = []
        response = request.execute()

        for item in response["items"]:
            videos.append(
                YoutubeVideo(
                    item["snippet"]["title"].split("|")[0].strip(),
                    f"https://www.youtube.com/watch?v={item['snippet']['resourceId']['videoId']}",
                )
            )

        return videos
