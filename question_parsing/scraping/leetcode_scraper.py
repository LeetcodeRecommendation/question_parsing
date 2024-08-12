import json

import httpx
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Final, Dict

from question_parsing import LOGGER_NAME


class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


@dataclass
class Question:
    question_name: str
    question_url: str
    difficulty: Difficulty
    solved: bool
    score: float
    company_name: List[str]


class LCScraper:
    REFERER: Final[str] = "https://leetcode.com"
    DIFF_STR_TO_DIFFICULTY: Final[Dict[str, Difficulty]] = {
        "EASY": Difficulty.EASY,
        "MEDIUM": Difficulty.MEDIUM,
        "HARD": Difficulty.HARD,
    }
    GRAPH_QL_COMPANY_QUERY: Final[str] = (
        "query favoriteQuestionListForCompany($favoriteSlug: String!,"
        " $filter: FavoriteQuestionFilterInput)"
        " { favoriteQuestionList(favoriteSlug: $favoriteSlug, filter: $filter)"
        " { questions { "
        "difficulty id paidOnly questionFrontendId status title titleSlug"
        " translatedTitle isInMyFavorites frequency topicTags "
        "{ name nameTranslated slug } } } }"
    )

    def __init__(self, cookie_session_id: str, csrf_cookie: str):
        self._log = logging.getLogger(LOGGER_NAME)
        self._cookie_session_id = cookie_session_id
        self._httpx_client = httpx.AsyncClient()
        self._csrf_cookie = csrf_cookie

    async def scan_leetcode(self, company_name: str) -> tuple[List[Question], str]:
        headers = {"Referer": LCScraper.REFERER, "X-Csrftoken": self._csrf_cookie}
        cookies = {
            "LEETCODE_SESSION": self._cookie_session_id,
            "csrftoken": self._csrf_cookie,
        }
        async with self._httpx_client as client:
            response = await client.post(
                "https://leetcode.com/graphql/",
                json={
                    "query": LCScraper.GRAPH_QL_COMPANY_QUERY,
                    "variables": {
                        "favoriteSlug": f"{company_name.lower()}-thirty-days",
                        "filter": {"positionRoleTagSlug": ""},
                    },
                    "operationName": "favoriteQuestionListForCompany",
                },
                headers=headers,
                cookies=cookies,
            )
        questions = json.loads(response.content)["data"]["favoriteQuestionList"][
            "questions"
        ]
        return [
            Question(
                question_name=question["title"],
                question_url=f"https://leetcode.com/problems/{question['titleSlug']}",
                difficulty=LCScraper.DIFF_STR_TO_DIFFICULTY[question["difficulty"]],
                solved=question["status"] == "SOLVED",
                score=question["frequency"],
                company_name=[company_name],
            )
            for question in questions
        ], company_name
