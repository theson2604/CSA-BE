import pytz
from datetime import datetime
from unidecode import unidecode
import random

def get_current_hcm_datetime() -> str:
    """
        Get the current Ho Chi Minh's datetime with format '2024-01-09 10:11:21'
    """
    timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    now = datetime.now(timezone)
    return now.strftime("%Y-%m-%d %H:%M:%S")

def convert_company_str(name: str = "") -> str:
    """
        Convert str "Nhựa Tiền Phong" into "nhuatienphong"
    """
    return unidecode(name).lower().replace(" ", "")


def generate_db_company(name: str = "") -> str:
    """
        Generate unique company's db with format "db_nhuatienphong_123"
    """
    rand_num = random.randint(0, 999)
    rand_3_digits = f"{rand_num:03}"
    return "db_" + convert_company_str(name) + f"_{rand_3_digits}"
    # return "db_" + convert_company_str(name) + f"_888"