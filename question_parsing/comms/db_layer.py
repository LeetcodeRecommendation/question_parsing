import asyncio
import logging
from typing import Final, Any, Dict, Union, Optional
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, PreparedStatement

from question_parsing import LOGGER_NAME
from question_parsing.scraping.leetcode_scraper import Question
from question_parsing.scraping.youtube_playlist import YoutubeVideo


class CassandraDB:
    KEYSPACE: Final[str] = "leetcode_rs"
    USER_QUESTIONS_TABLE: Final[str] = "user_questions"
    USER_VIDEOS_TABLE: Final[str] = "user_videos"

    def __init__(self, cassandra_ips: list[str]):
        self._log = logging.getLogger(LOGGER_NAME)
        self._cluster = Cluster(cassandra_ips)
        self._session = self._cluster.connect(keyspace=CassandraDB.KEYSPACE)
        self._async_lock = asyncio.Lock()
        self._add_question_query = self._session.prepare(
            f"INSERT INTO {CassandraDB.USER_QUESTIONS_TABLE} (user_name, question_name, question_url, score, difficulty, company_names, manually_marked_by_user, solved) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )
        self._add_video = self._session.prepare(
            f"INSERT INTO {CassandraDB.USER_VIDEOS_TABLE} (user_name, video_name, video_url, watched) VALUES (?, ?, ?, ?)"
        )

    async def run_statement(
        self,
        query: Union[SimpleStatement | PreparedStatement],
        parameters: Optional[Dict[str, Any]] = None,
    ):
        return await asyncio.get_running_loop().run_in_executor(
            None, self._session.execute, query, parameters
        )

    async def update_user_leet_code_questions(
        self, user_name: str, questions: list[Question]
    ):
        self._log.info(f"updating lc questions for user {user_name}")
        for question in questions:
            async with self._async_lock:
                insert_params = (
                    user_name,
                    question.question_name,
                    question.question_url,
                    question.score,
                    question.difficulty.value,
                    question.company_name,
                    False,
                    question.solved,
                )

                await self.run_statement(self._add_question_query.bind(insert_params))

    async def update_user_youtube_videos(
        self, user_name: str, youtube_videos: list[YoutubeVideo]
    ):
        select_statement = SimpleStatement(
            f"""
            SELECT user_name, video_name FROM {CassandraDB.USER_VIDEOS_TABLE} WHERE user_name = %(uname)s AND video_name = %(vname)s
        """
        )
        self._log.info(f"updating youtube videos for user {user_name}")

        for video in youtube_videos:
            async with self._async_lock:
                rows = await self.run_statement(
                    select_statement,
                    parameters={"uname": user_name, "vname": video.title},
                )
                if not rows:
                    insert_params = (user_name, video.title, video.url, False)

                    await self.run_statement(self._add_video.bind(insert_params))
