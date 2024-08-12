from typing import List

import pydantic


class UserRecommendationRefreshRequest(pydantic.BaseModel):
    name: str
    token: str
    csrfToken: str
    companies: List[str]


class UserRecommendationRefreshResponse(pydantic.BaseModel):
    name: str
