import re
from FieldObject.repository import FieldObjectRepository
from MailService.models import EmailModel, TemplateModel
from MailService.repository import MailServiceRepository
from MailService.schemas import *
from abc import ABC, abstractmethod
from RecordObject.models import RecordObjectModel
from RecordObject.services import RecordObjectService
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
            key = Random.new().read(int(os.environ.get("KEY_BYTES")))
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

    def get_field_id(src):
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
    
    async def field_id_to_field_value(self, mail_body, field_ids, record):
        for i in range(len(field_ids)):
            print("REPLACE")
            field_id = field_ids[i]
            if field_id[0] != "f":
                content = (await self.template_repo.find_template_by_id(field_id)).get("body")
                print(content)
            else: content = record.get(field_id)
            mail_body = mail_body.replace(f"@{field_id}", content)
        return mail_body
    
    def get_bodies(template: str) -> List[str]:
        bodies = []
        field_ids, positions = MailServices.get_field_id(template)

        # case start of string is NOT a field_id -> get body before the first field_id
        if positions[0] != 0:
            body = template[0:positions[0]]
            bodies.append(body)

        for i in range(len(positions)-1):
            body = template[positions[i]+len(field_ids[i])+1:positions[i+1]]
            bodies.append(body)

        # if there's still content after the last field_id
        if positions[-1]+len(field_ids[-1])+1 < len(template):
            body = template[positions[-1]+len(field_ids[-1])+1: len(template)]
            bodies.append(body)

        return bodies
        

    # TODO LATER
    def match_template(template: str, text: str, bodies: List[str]) -> bool:
        template = template.replace("\n", "")
        text = text.replace("\r\n","")
        raise HTTPBadRequest(f"{text} |||||||||||||| {template}")
        field_ids, positions = MailServices.get_field_id(template)

        # case start of string is NOT a field_id -> get body before the first field_id
        if positions[0] != 0:
            body = template[0:positions[0]]
            bodies.append(body)

        for i in range(len(positions)-1):
            body = template[positions[i]+len(field_ids[i])+1:positions[i+1]]
            bodies.append(body)

        # if there's still content after the last field_id
        if positions[-1]+len(field_ids[-1])+1 < len(template):
            body = template[positions[-1]+len(field_ids[-1])+1: len(template)]
            bodies.append(body)
        try:
            idx = -1
            for body in bodies:
                new_idx = text.index(body)
                if new_idx <= idx:
                    return False
                else:
                    idx = new_idx
            return True
        except:
            return False

    def get_field_value_from_text(template: str, text: str, bodies: List[str]) -> dict:
        field_ids, positions = MailServices.get_field_id(template)
        contents = {}
        # case start of string is a field_id
        if positions[0] == 0:
            idx_next = text.index(bodies[0])
            content = text[0:idx_next]
            contents[field_ids[0]] = content

        payload = -1 if len(bodies) > len(field_ids) else 0
        for i in range(len(bodies)-1):
            idx = text.index(bodies[i])
            idx_next = text.index(bodies[i+1])
            content = text[idx+len(bodies[i]):idx_next]
            contents[field_ids[i+1+payload]] = content

        # if template ends with a field_id
        if positions[-1]+len(field_ids[-1])+1 == len(template):
            idx = text.index(bodies[-1])
            content = text[idx+len(bodies[-1]):]
            contents[field_ids[-1]] = content

        return contents
    
    def get_new_body_gmail(msg):
        matching_string_obj = re.search(r"\w+\s+\w+[,]\s+\w+\s+\d+[,]\s+\d+\s+\w+\s+\d+[:]\d+\s+\w+.*", msg)
        if matching_string_obj:
            body_list = msg.split(matching_string_obj.group())
            body = body_list[0] # index 0 is new body, index 1 is old body
        return body

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

        password = email_obj.get("pwd")
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
                smtp_server.login(address, password)
        except smtplib.SMTPAuthenticationError:
            raise HTTPBadRequest("Invalid email or password")
        
        key, iv, ciphertext = self.encrypt_aes(password)
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
        email = mail.get("email")
        mail_pwd = await self.get_mail_pwd(email, admin_id)

        template = await self.template_repo.find_template_by_id(mail.get("template"))
        if not template:
            raise HTTPBadRequest(f"Can not find template")
        if template.get("type") != "send":
            raise HTTPBadRequest(f"Invalid template type {template.get("type")}")

        object_id = template.get("object_id")
        object = await self.obj_repo.find_one_by_id(object_id)
        if not object:
            raise HTTPBadRequest(f"Can not find object")
            
        obj_id = object.get("obj_id")
        record = (await self.record_repo.get_one_by_id_with_parsing_ref_detail(mail.get("record"), object_id))[0]
        fd_id = (await self.field_obj_repo.find_one_by_field_type(object_id, "id")).get("field_id")

        """
        body
        hello Mr.@fd_name_758, l123oihsdaf;
        """
        
        mail_body = template.get("body")
        mail_subject = template.get("subject")
        field_ids_subject, postions = MailServices.get_field_id(mail_subject)
        field_ids_body, postions = MailServices.get_field_id(mail_body)
        print(field_ids_body)
        if len(field_ids_subject) != 0:
            mail_subject = await self.field_id_to_field_value(mail_subject, field_ids_subject, record)
        mail_subject = f"[{obj_id.replace('obj_','').upper()}.{record.get(fd_id)}] " + mail_subject
        mail_body = await self.field_id_to_field_value(mail_body, field_ids_body, record)

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
        # mail = mail.model_dump()
        email = mail.get("email")
        mail_pwd = await self.get_mail_pwd(email, admin_id)

        template = await self.template_repo.find_template_by_id(mail.get("template"))
        if not template:
            raise HTTPBadRequest(f"Can not find template")
        
        mail_contents = [] #List[dict]

        # bodies = MailServices.get_bodies(template.get("body"))
        with MailBox("imap.gmail.com").login(email, mail_pwd, 'INBOX') as mailbox:
            for msg in mailbox.fetch(AND(date_gte=get_current_hcm_date(), subject=r"re\*", seen=False), mark_seen=False):
                content = {}
                text = MailServices.get_new_body_gmail(msg.text)
                content["from"] = msg.from_
                content["body"] = text

                # if MailServices.match_template(template.get("body"), text, bodies):
                #     print("AKLSDJASHFWUI#RHO")
                subject = msg.subject
                meta_data = subject[subject.index("[")+1 : subject.index("]")]
                obj, prefix_id = meta_data.split(".")
                obj_id_str = f"obj_{obj.lower()}" # ref collection
                content["ref_obj_id"] = obj_id_str
                mail_contents.append(content)

                # TODO AFTER INTEGRATING TO WORKLOW, LET CUSTOMER CONFIG REF PARENT FIELD
                # obj_id = (await self.obj_repo.find_one_by_object_id(obj_id_str)).get("_id")
                # ref_record_repo = RecordObjectRepository(self.db_str, obj_id_str)
                # fd_id = (await self.field_obj_repo.find_one_by_field_type(obj_id, "id")).get("field_id")
                
                # ref_record_id = (await ref_record_repo.find_one({fd_id: prefix_id})).get("_id")

                # IF NEED TO INSERT RECORD
                # new_record = MailServices.get_field_value_from_text(template.get("body"), text, bodies)
                # new_record = {"fd_content_790": text, "fd_score_034": 9, "object_id": template.get("object_id")}
                # object = (await self.obj_repo.find_one_by_id(template.get("object_id"))) # current collection
                # obj_id_str = object.get("obj_id")
                # record_services = RecordObjectService(self.db_str, obj_id_str, template.get("object_id"))
                # result = await record_services.create_record(new_record, admin_id)
                # return result
                    
                # print("SUBJECT: ", msg.subject)
                # print("BODY: ", msg.text)
        return mail_contents
    