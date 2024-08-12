import asyncio

from dotenv import load_dotenv

from question_parsing import LOGGER_NAME
from question_parsing.comms.kafka_streams import KafkaStreams
from question_parsing.utils.environment import Environment
from question_parsing.utils.logging import initialize_logger


def main():
    load_dotenv()
    initialize_logger(LOGGER_NAME)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    kafka_streams = KafkaStreams(Environment.get_kafka_servers(), loop)
    loop.run_until_complete(kafka_streams.consume_topics())


if __name__ == "__main__":
    main()
