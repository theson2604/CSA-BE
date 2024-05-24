from elasticsearch import AsyncElasticsearch
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchBase:
    def __init__(self):
        self.es = AsyncElasticsearch(
            [os.environ.get("ELASTIC_HOST")],
            basic_auth=(
                os.environ.get("ELASTIC_USERNAME"),
                os.environ.get("ELASTIC_PASSWORD"),
            ),
            ca_certs=os.environ.get("CERT_FILE"),
            timeout=60
        )

    async def health_check(self) -> bool:
        await self.es.cluster.health()
        return True
