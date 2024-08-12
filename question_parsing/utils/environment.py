import os


class Environment:
    @staticmethod
    def get_youtube_token() -> str:
        return os.environ["YOUTUBE_TOKEN"]

    @staticmethod
    def get_cassandra_url() -> list[str]:
        return os.environ["CASSANDRA_URL"].split(";")

    @staticmethod
    def get_redis_ip() -> str:
        return os.environ["REDIS_IP"]

    @staticmethod
    def get_redis_port() -> int:
        return int(os.environ["REDIS_PORT"])

    @staticmethod
    def get_kafka_servers() -> str:
        return os.environ["KAFKA_SERVERS"]
