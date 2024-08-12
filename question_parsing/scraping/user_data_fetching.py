import asyncio
import logging
from typing import List, Final

from question_parsing import LOGGER_NAME
from question_parsing.scraping.leetcode_scraper import Question, LCScraper
from question_parsing.scraping.youtube_playlist import YoutubeVideo, YoutubeProgress


class UserDataFetching:
    MAX_CONCURRENT_SCRAPPERS: Final[int] = 2
    SLEEP_BETWEEN_SCRAPER_FETCH_IN_SEC: Final[int] = 2

    def __init__(self):
        self._log = logging.getLogger(LOGGER_NAME)

    async def _scrape_leetcode(
        self, leetcode_cookie: str, csrf_cookie: str, company_names: list[str]
    ) -> list[Question]:
        questions: dict[str, Question] = dict()
        futures = []
        for company in company_names:
            scraper = LCScraper(leetcode_cookie, csrf_cookie)
            futures.append(asyncio.create_task(scraper.scan_leetcode(company)))

        for future in futures:
            res_questions, company = await future
            for question in res_questions:
                if question.question_name not in questions:
                    questions[question.question_name] = question
                else:
                    questions[question.question_name].score += question.score
                    questions[question.question_name].company_name.append(company)

        return list(questions.values())

    async def get_user_details(
        self,
        leetcode_cookie: str,
        csrf_cookie: str,
        youtube_token: str,
        company_names: list[str],
    ) -> tuple[List[Question], List[YoutubeVideo]]:
        youtube_videos = await asyncio.get_running_loop().run_in_executor(
            None, YoutubeProgress.get_youtube_playlist, youtube_token
        )
        leetcode_questions = await self._scrape_leetcode(
            leetcode_cookie, csrf_cookie, company_names
        )
        return leetcode_questions, youtube_videos
