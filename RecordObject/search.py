from typing import List
from Object.repository import ObjectRepository
from RecordObject.constants import CustomAnalyzer
from RecordObject.repository import RecordObjectRepository
from app.common.elastic import ElasticsearchBase
from app.common.enums import FieldObjectType
from elasticsearch.helpers import async_bulk


class ElasticsearchRecord(ElasticsearchBase):
    def __init__(self, db_str: str, obj_id_str: str, obj_id: str):
        super().__init__()
        self.obj_index = f"{db_str}.{obj_id_str}"
        self.obj_id = obj_id
        self.record_repo = RecordObjectRepository(db_str, coll=obj_id_str)
        self.obj_repo = ObjectRepository(db_str)

    async def search_record(
        self, query: dict, page: int = 1, page_size: int = 10
    ) -> List[dict]:
        matching_fields = []
        skip = (page - 1) * page_size
        for field_id, query_str in query.items():
            matching_fields.append({"match": {field_id: query_str}})

        response = await self.es.search(
            index=self.obj_index,
            body={"query": {"bool": {"must": matching_fields}}},
            stored_fields=[],
            from_=skip,
            size=page_size,
        )

        result = response.get("hits", {"hits": []}).get("hits")
        record_ids = [o.get("_id") for o in result]
        return await self.record_repo.get_many_by_ids_with_parsing_ref_detail(
            record_ids, self.obj_id
        )

    async def index_doc(self, record_id: str, doc: dict):
        await self.es.index(index=self.obj_indexing, id=record_id, document=doc)

    async def create_obj_index(self):
        settings = {
            "analysis": {
                "analyzer": self.get_analyzer_config(),
                "tokenizer": self.get_tokenizer_config(),
            }
        }
        mappings = {"properties": await self.parse_mappings()}

        await self.es.indices.create(
            index=self.obj_index, settings=settings, mappings=mappings
        )

    async def gen_docs(self):
        records = await self.record_repo.find_all()
        for record in records:
            yield {
                "_index": self.obj_index,
                "_id": record.pop("_id"),
                "_source": record,
            }

    async def sync_docs(self) -> bool:
        """health check and sync records from Mongodb"""
        await self.health_check()
        if not await self.es.indices.exists(index=self.obj_index):
            await self.create_obj_index()
            await async_bulk(self.es, self.gen_docs())

        elif await self.es.indices.exists(index=self.obj_index):
            count_docs = await self.es.count(index=self.obj_index)
            count_docs = count_docs["count"]
            count_records = await self.record_repo.count_all()
            if count_docs != count_records:
                await self.es.indices.delete(index=self.obj_index)
                await self.create_obj_index()
                await async_bulk(self.es, self.gen_docs())

        return True

    async def parse_mappings(self):
        obj_detail = await self.obj_repo.get_object_with_all_fields(self.obj_id)
        mappings = {}
        for field in obj_detail.get("fields"):
            mapping_analyzer = self.get_mapping_by_field_type(field.get("field_type"))
            if (
                mapping_analyzer is CustomAnalyzer.AUTOCOMPLETE_VI_TEXT
                or CustomAnalyzer.AUTOCOMPLETE_EMAIL
            ):
                mappings[field.get("field_id")] = {
                    "type": "text",
                    "analyzer": mapping_analyzer.value,
                    "search_analyzer": CustomAnalyzer.AUTOCOMPLETE_SEARCH.value,
                }

            elif mapping_analyzer is CustomAnalyzer.AUTOCOMPLETE_PHONENUMBER:
                mappings[field.get("field_id")] = {
                    "type": "text",
                    "analyzer": CustomAnalyzer.AUTOCOMPLETE_PHONENUMBER.value,
                    "search_analyzer": CustomAnalyzer.STANDARD.value,
                }
            elif mapping_analyzer is CustomAnalyzer.STANDARD:
                mappings[field.get("field_id")] = {
                    "type": "text",
                    "analyzer": CustomAnalyzer.STANDARD.value,
                }

        return mappings

    def get_mapping_by_field_type(self, field_type: FieldObjectType):
        mappings = {
            FieldObjectType.ID: CustomAnalyzer.STANDARD,
            FieldObjectType.TEXT: CustomAnalyzer.AUTOCOMPLETE_VI_TEXT,
            FieldObjectType.TEXTAREA: CustomAnalyzer.STANDARD,
            FieldObjectType.EMAIL: CustomAnalyzer.AUTOCOMPLETE_EMAIL,
            FieldObjectType.SELECT: CustomAnalyzer.AUTOCOMPLETE_VI_TEXT,
        }

        return mappings[field_type]

    def get_analyzer_config(self):
        return {
            CustomAnalyzer.AUTOCOMPLETE_VI_TEXT.value: {
                "tokenizer": CustomAnalyzer.AUTOCOMPLETE_VI_TEXT.value,
                "filter": ["lowercase"],
            },
            CustomAnalyzer.AUTOCOMPLETE_EMAIL.value: {
                "tokenizer": CustomAnalyzer.AUTOCOMPLETE_EMAIL.value,
                "filter": ["lowercase"],
            },
            CustomAnalyzer.AUTOCOMPLETE_PHONENUMBER.value: {
                "tokenizer": CustomAnalyzer.AUTOCOMPLETE_PHONENUMBER.value,
                "filter": ["lowercase"],
            },
            CustomAnalyzer.AUTOCOMPLETE_SEARCH.value: {"tokenizer": "lowercase"},
        }

    def get_tokenizer_config(self):
        return {
            CustomAnalyzer.AUTOCOMPLETE_VI_TEXT.value: {
                "type": "edge_ngram",
                "min_gram": 1,
                "max_gram": 8,
                "token_chars": ["letter", "digit"],
            },
            CustomAnalyzer.AUTOCOMPLETE_EMAIL.value: {
                "type": "edge_ngram",
                "min_gram": 1,
                "max_gram": 64,
                "token_chars": ["letter", "digit"],
            },
            CustomAnalyzer.AUTOCOMPLETE_PHONENUMBER.value: {
                "type": "edge_ngram",
                "min_gram": 1,
                "max_gram": 11,
                "token_chars": ["letter", "digit"],
            },
        }
