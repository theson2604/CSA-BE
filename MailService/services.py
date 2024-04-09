from MailService.models import EmailModel, TemplateModel
from MailService.repository import MailServiceRepository
from MailService.schemas import *
from abc import ABC, abstractmethod
from app.common.db_connector import DBCollections
from app.common.errors import HTTPBadRequest
from app.settings.config import KEY_BYTES
# from fastapi import Depends
from bson import ObjectId
from Object.repository import ObjectRepository
from RootAdministrator.repository import RootAdministratorRepository
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random
from email.mime.text import MIMEText
import binascii
import smtplib

class IMailServices(ABC):
    @abstractmethod
    def encrypt_aes(self, pwd: str):
        raise NotImplementedError
    
    @abstractmethod
    def decrypt_aes(self, key: str, iv: bytes, pwd: str):
        raise NotImplementedError
    
    @abstractmethod
    async def create_email(self, email: EmailSchema) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def send_one(self, mail: SendMailSchema) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def get_mail_pwd(self, email: str, admin_id: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    async def create_template(self) -> bool:
        raise NotImplementedError

class MailServices(IMailServices):
    def __init__(self, db):
        self.repo = MailServiceRepository()
        self.template_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        self.root_repo = RootAdministratorRepository()
        self.obj_repo = ObjectRepository(db)

        self.db_str = db

    def encrypt_aes(self, pwd: str):
        try:
            key = Random.new().read(KEY_BYTES)
            iv = Random.new().read(AES.block_size)
                                
            iv_int = int(binascii.hexlify(iv), 16)
            ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)
            aes = AES.new(key, AES.MODE_CTR, counter=ctr)
            ciphertext = aes.encrypt(pwd.encode("utf-8"))
            return key, iv, ciphertext
        
        except Exception as e:
            print(f"Encryption error: {e}")
            raise Exception("error in encrypt")
    
    def decrypt_aes(self, key, iv, ciphertext):
        try:
            iv_int = int.from_bytes(iv, byteorder="big")
            ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

            aes = AES.new(key, AES.MODE_CTR, counter=ctr)
            return aes.decrypt(ciphertext).decode("utf-8")
        except Exception as e:
            print(f"Decryption error: {e}")
            raise Exception("error in decrypt")


    async def create_email(self, email: EmailSchema):
        email_obj = email.model_dump()
        admin_id = email_obj.get("admin")
        address = email_obj.get("email")
        registered_email = await self.repo.find_email_by_name(address)
        if registered_email:
            raise HTTPBadRequest(f"Email {address} has been registed")

        system_admin = await self.root_repo.find_one_by_id(admin_id, self.db_str)
        if not system_admin:
            raise HTTPBadRequest("Cannot find system admin by admin_id")

        key, iv, ciphertext = self.encrypt_aes(email_obj.get("pwd"))

        record = EmailModel(
            _id = str(ObjectId()),
            email = address,
            pwd = ciphertext,
            key = key,
            iv = iv,
            admin = admin_id
        )

        await self.repo.insert_email(record.model_dump(by_alias=True))
        return True
    
    async def send_one(self, mail: SendMailSchema, admin_id: str) -> str:
        mail = mail.model_dump()
        email = mail.get("send_from")
        mail_model = MIMEText(mail.get("content"))
        mail_model["Subject"] = mail.get("subject")
        mail_model["From"] = email
        mail_model["To"] = ",".join(mail.get("send_to"))
        mail_pwd = await self.get_mail_pwd(email, admin_id)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(email, mail_pwd)
            smtp_server.sendmail(email, mail.get("send_to"), mail_model.as_string())
        return "Message sent!"
    
    async def get_mail_pwd(self, email: str, admin_id: str) -> str:
        result = await self.repo.find_email({"email": email, "admin_id": admin_id}, projection={"modified_at": 0, "created_at": 0})
        if not result:
            raise HTTPBadRequest("Cannot find email")
        return self.decrypt_aes(result.get("key"), result.get("iv"), result.get("pwd"))

    async def create_template(self, template: TemplateSchema) -> str:
        template = template.model_dump()
        object_id = template.get("object")
        ref_obj = await self.obj_repo.find_one_by_id(object_id)
        if not ref_obj:
            raise HTTPBadRequest(f"Not found ref_obj {object_id}.")

        record = TemplateModel(
            _id = str(ObjectId()),
            name = template.get("name"),
            object_id = object_id,
            subject = template.get("subject"),
            body = template.get("body")
        )
        
        await self.template_repo.insert_template(record.model_dump(by_alias=True))
        return True