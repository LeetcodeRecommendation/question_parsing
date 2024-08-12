import asyncio
import json
import logging
import traceback
from json import JSONDecodeError

import aiokafka
from pydantic import ValidationError

from question_parsing import LOGGER_NAME
from question_parsing.comms.cache_layer import RedisCache
from question_parsing.comms.db_layer import CassandraDB
from question_parsing.scraping.user_data_fetching import UserDataFetching
from question_parsing.utils.environment import Environment
from question_parsing.utils.messages import (
    UserRecommendationRefreshRequest,
    UserRecommendationRefreshResponse,
)


class KafkaStreams:
    def __init__(self, kafka_urls: str, event_loop):
        self._log = logging.getLogger(LOGGER_NAME)
        self._consumer = aiokafka.AIOKafkaConsumer(
            "rs_request_topic",
            bootstrap_servers=kafka_urls.split(";"),
            enable_auto_commit=False,
            group_id="requests_groups",
            loop=event_loop,
        )
        self._producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=kafka_urls.split(";"), loop=event_loop
        )
        self._user_data_fetching = UserDataFetching()
        self._db_layer = CassandraDB(Environment.get_cassandra_url())
        self._cache_layer = RedisCache(
            Environment.get_redis_ip(), Environment.get_redis_port()
        )

    async def consume_topics(self):
        await self._consumer.start()
        await self._producer.start()
        while True:
            async for msg in self._consumer:
                request = None
                try:
                    request = UserRecommendationRefreshRequest(**json.loads(msg.value))
                    self._log.info("received request to get user recommendations")
                    (
                        questions,
                        youtube_videos,
                    ) = await self._user_data_fetching.get_user_details(
                        request.token,
                        request.csrfToken,
                        Environment.get_youtube_token(),
                        request.companies,
                    )

                    await self._db_layer.update_user_leet_code_questions(
                        request.name, questions
                    )
                    await self._db_layer.update_user_youtube_videos(
                        request.name, youtube_videos
                    )
                    await self._cache_layer.invalidate_user(user=request.name)
                except (JSONDecodeError, ValidationError):
                    self._log.error(f"Received unparsable message: {msg.value}")

                except Exception as e:
                    self._log.error(f"Internal server error for: {msg.value}, {e}")
                    traceback.print_exc()
                finally:
                    if request is not None:
                        await self._producer.send_and_wait(
                            "rs_response_topic",
                            UserRecommendationRefreshResponse(name=request.name)
                            .model_dump_json()
                            .encode(),
                        )
                    await self._consumer.commit()
