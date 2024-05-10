import asyncio
from elasticsearch import AsyncElasticsearch, Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()
class ElasticsearchBase:
    def __init__(self):
        self.es = AsyncElasticsearch(
            [os.environ.get("ELASTIC_HOST")],
            basic_auth=(os.environ.get("ELASTIC_USERNAME"), os.environ.get("ELASTIC_PASSWORD")),
            ca_certs=f"{os.environ.get("ROOT_DIR")}\ca.crt",
        )

    async def health_check(self) -> bool:
        await self.es.cluster.health()
        return True
