from pymongo import ReturnDocument
import pytz
from datetime import datetime
from unidecode import unidecode
import random
from app.common.db_connector import DBCollections, client


def get_current_hcm_datetime() -> str:
    """
    Get the current Ho Chi Minh's datetime with format '2024-01-09 10:11:21'
    """
    timezone = pytz.timezone("Asia/Ho_Chi_Minh")
    now = datetime.now(timezone)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def get_current_hcm_date() -> datetime.date:
    """
    Get the current Ho Chi Minh's date with format '2024-01-09'
    """
    timezone = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(timezone).date()


def convert_str(name: str = "") -> str:
    """
    Convert str "Nhựa Tiền Phong" into "nhuatienphong"
    """
    return unidecode(name).lower().replace(" ", "")


def generate_model_id(name: str = "") -> str:
    rand_num = random.randint(0, 999999)
    rand_6_digits = f"{rand_num:06}"
    return "model_" + convert_str(name) + f"_{rand_6_digits}"


def generate_db_company(name: str = "") -> str:
    """
    Generate unique company's db with format "db_nhuatienphong_123456"
    """
    rand_num = random.randint(0, 999999)
    rand_6_digits = f"{rand_num:06}"
    return "db_" + convert_str(name) + f"_{rand_6_digits}"


def generate_field_id(name: str = "") -> str:
    """
    Generate unique Object's Field with format "fd_customername_123456"
    """
    rand_num = random.randint(0, 999999)
    rand_6_digits = f"{rand_num:06}"
    return "fd_" + convert_str(name) + f"_{rand_6_digits}"


def generate_object_id(name: str = "") -> str:
    """
    Generate unique Object's Field with format "obj_customercare_123456"
    """
    rand_num = random.randint(0, 999999)
    rand_6_digits = f"{rand_num:06}"
    return "obj_" + convert_str(name) + f"_{rand_6_digits}"


async def generate_next_record_id(db_str: str, obj_id: str):
    """
    :Params:
    - obj_id: _id
    """
    counter_coll = client.get_database(db_str).get_collection(
        DBCollections.RECORD_COUNTER
    )

    return await counter_coll.find_one_and_update(
        {"_id": obj_id}, {"$inc": {"seq": 1}}, upsert=True, return_document=ReturnDocument.AFTER
    )

async def get_current_record_id(db_str: str, obj_id: str):
    """
    :Params:
    - obj_id: _id
    """
    counter_coll = client.get_database(db_str).get_collection(
        DBCollections.RECORD_COUNTER
    )

    record = await counter_coll.find_one(
        {"_id": obj_id}
    )

    if not record:
        await counter_coll.insert_one({"_id": obj_id, "seq": 1})
        return {"_id": obj_id, "seq": 1}
    
    return record

async def update_record_id(db_str: str, obj_id: str, seq: int):
    """
    :Params:
    - obj_id: _id
    """
    counter_coll = client.get_database(db_str).get_collection(
        DBCollections.RECORD_COUNTER
    )

    filter = {"_id": obj_id}
    new_value = {"$set": {"seq": seq}}

    return await counter_coll.update_one(filter, new_value)