import re
from FieldObject.repository import FieldObjectRepository
from MailService.models import EmailModel, TemplateModel
from MailService.repository import MailServiceRepository
from MailService.schemas import *
from abc import ABC, abstractmethod
from app.common.db_connector import DBCollections
from app.common.errors import HTTPBadRequest
# from fastapi import Depends
from bson import ObjectId
from Object.repository import ObjectRepository
from RecordObject.repository import RecordObjectRepository
from RootAdministrator.repository import RootAdministratorRepository
from Crypto.Cipher import AES
from Crypto.Util import Counter
from Crypto import Random
from email.mime.text import MIMEText
from imap_tools import MailBox, AND
import binascii
import smtplib
from dotenv import load_dotenv
import os

from app.common.utils import get_current_hcm_date

load_dotenv()

class MailServices:
    def __init__(self, db, coll: str = None):
        self.repo = MailServiceRepository()
        self.template_repo = MailServiceRepository(db, DBCollections.EMAIL_TEMPLATE)
        self.root_repo = RootAdministratorRepository()
        self.obj_repo = ObjectRepository(db)
        self.field_obj_repo = FieldObjectRepository(db)
        if coll != None:
            self.record_repo = RecordObjectRepository(db, coll)

        self.db_str = db

    def encrypt_aes(self, pwd: str):
        try:
            key = Random.new().read(os.environ.get("KEY_BYTES"))
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

    def get_field_id(self, src):
        positions = []
        for i in range(len(src)):
            if src[i] == "@":
                positions.append(i)
        print(positions)
        field_ids = ["" for _ in range(len(positions))]
        for idx in range(len(positions)):
            i = positions[idx]
            while i+1 < len(src) and (src[i+1].isalnum() or src[i+1] == "_"):
                i += 1
                field_ids[idx] += (src[i])
            idx = i
        return field_ids, positions
    
    def field_id_to_field_value(mail_body, field_ids, record):
        for i in range(0, len(field_ids)):
            print("REPLACE")
            field_id = f"@{field_ids[i]}"
            content = record[0].get(f"{field_ids[i]}")
            mail_body = mail_body.replace(field_id, content)
            return mail_body

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
        mail_pwd = await self.get_mail_pwd(email, admin_id)

        template = await self.template_repo.find_template_by_id(mail.get("template"))
        if not template:
            raise HTTPBadRequest(f"Can not find template")

        record = await self.record_repo.get_one_by_id_with_parsing_ref_detail(mail.get("record"), template.get("object_id"))
        if not record:
            raise HTTPBadRequest("NONE")

        """
        body
        hello Mr.@fd_name_758, l123oihsdaf;
        """
        
        mail_body = template.get("body")
        mail_subject = template.get("subject")
        field_ids_subject, postions = self.get_field_id(mail_subject)
        field_ids_body, postions = self.get_field_id(mail_body)
        mail_subject = MailServices.field_id_to_field_value(mail_subject, field_ids_subject, record)
        mail_body = MailServices.field_id_to_field_value(mail_body, field_ids_body, record)

        mail_model = MIMEText(mail_body)
        mail_model["Subject"] = mail_subject
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

    async def create_template(self, template) -> str:
        template = template.model_dump()
        object_id = template.get("object")
        ref_obj = await self.obj_repo.find_one_by_id(object_id)
        if not ref_obj:
            raise HTTPBadRequest(f"Not found ref_obj {object_id}.")

        type = template.get("type")
        record = {
            "_id": str(ObjectId()),
            "name": template.get("name"),
            "object_id": object_id,
            "body": template.get("body"),
            "type": type
        }
        if type == "send":
            record["subject"] = template.get("subject")

        await self.template_repo.insert_template(TemplateModel.model_validate(record).model_dump(by_alias=True))
        return True
    
    async def get_all_templates(self) -> List:
        return await self.template_repo.get_all_templates()
    
    async def get_templates_by_object_id(self, object_id) -> List:
        return await self.template_repo.get_templates_by_object_id(object_id)
    
    async def scan_email(self, mail: MailSchema, admin_id: str):
        mail = mail.model_dump()
        email = mail.get("send_from")
        mail_pwd = await self.get_mail_pwd(email, admin_id)

        template = await self.template_repo.find_template_by_id(mail.get("template"))
        if not template:
            raise HTTPBadRequest(f"Can not find template")
        
        # object_id = mail.get("object_id") # object to 
        # fd_email = self.field_obj_repo.find_one
        
        with MailBox("imap.gmail.com").login(email, mail_pwd, 'INBOX') as mailbox:
            for msg in mailbox.fetch(AND(date_gte=get_current_hcm_date(), subject=r"re\*", seen=False)):
                # create new record if mail body match template
                if MailServices.match_template(template.get("body"), msg.txt):
                    subject = msg.subject
                    meta_data = subject[subject.index("[")+1 : subject.index("]")]
                    obj_id, prefix_id = meta_data.split(".")
                    ref_record_repo = RecordObjectRepository(self.db_str, obj_id)
                    field_ids = list((await ref_record_repo.find_one()).keys())
                    regex = r"fd_id_\d{3}"
                    fd_id = None
                    for field_id in field_ids:
                        if re.match(regex, field_id):
                            fd_id = field_id
                    ref_record_id = (await ref_record_repo.find_one({fd_id: prefix_id})).get("_id")

                    

                    pass
                print("SUBJECT: ", msg.subject)
                print("BODY: ", msg.text)
        return
    
    def match_template(template_body: str, mail_body: str) -> bool:
        return True