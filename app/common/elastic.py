import asyncio
from elasticsearch import AsyncElasticsearch, Elasticsearch

from app.settings.config import (
    ELASTIC_HOST,
    ELASTIC_PASSWORD,
    ELASTIC_USERNAME,
    ROOT_DIR,
)

class ElasticsearchBase:
    def __init__(self):
        self.es = AsyncElasticsearch(
            [ELASTIC_HOST],
            basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
            ca_certs=f"{ROOT_DIR}\ca.crt",
        )

    async def health_check(self) -> bool:
        await self.es.cluster.health()
        return True
