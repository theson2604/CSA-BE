import re
from FieldObject.repository import FieldObjectRepository
from MailService.models import EmailModel, TemplateModel
from MailService.repository import MailServiceRepository
from MailService.schemas import *
from Workflow.repository import WorkflowRepository
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
        self.workflow_repo = WorkflowRepository(db)
        if coll != None:
            self.scan_repo = MailServiceRepository(db, coll)
            self.record_repo = RecordObjectRepository(db, coll)

        self.db_str = db

    async def change_config(self):
        return await self.scan_repo.update_one_by_id("6655bf29be4cf0c9e2858287", {"email": "r123@gmail.com", "password": "123"})
    
    async def get_config(self, id):
        return await self.scan_repo.find_one_by_id(id)

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
        field_regex = r"@fd_\w+_\d{3}"
        ref_field_regex = r"@obj_\w+_\d{3}.fd_email_\d{3}"
        field_matches = re.finditer(field_regex, src)
        ref_field_matches = re.finditer(ref_field_regex, src)
        positions = []
        field_ids = []
        for field_match in field_matches:
            field_ids.append(field_match.group())
            positions.append(field_match.start())
        for ref_field_match in ref_field_matches:
            field_ids.append(ref_field_match.group())
            positions.append(ref_field_match.start())
        return field_ids, positions
    
    async def field_id_to_field_value(self, mail_body, field_ids, record):
        for i, field_id in enumerate(field_ids):
            if field_id[1] != "f":
                fd_ref, _, fd_id = field_id.split(".")
                content = record.get(fd_ref[1:]).get("ref_to").get(fd_id)
            else: content = record.get(field_id[1:])
            if not content: content = ""
            mail_body = mail_body.replace(field_id, content)
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
        matching_string_obj = re.search(r"\w+\s+\w+[,]\s+\w+\s+\d+[,]\s+\d+\s+\w+\s+\d+[:]\d+.*", msg)
        if matching_string_obj:
            body_list = msg.split(matching_string_obj.group())
            body = body_list[0] # index 0 is new body, index 1 is old body
        if not body:
            raise HTTPBadRequest("FAIL TO GET NEW BODY")
        return body

    async def create_email(self, email: EmailSchema, admin_id: str):
        email_obj = email.model_dump()
        db_str = email_obj.get("db_str")
        address = email_obj.get("email")
        registered_email = await self.repo.find_email_by_name(address)
        if registered_email:
            raise HTTPBadRequest(f"Email {address} has been registed")

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
            admin_id = admin_id,
            pwd = ciphertext,
            key = key,
            iv = iv,
            db = db_str,
            template_id = email_obj.get("template_id")
        )

        return await self.repo.insert_email(record.model_dump(by_alias=True))
    
    async def send_one(self, mail: SendMailSchema, db_str: str, record: dict) -> str:
        # mail = mail.model_dump()
        email = mail.get("email")
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
        # record = (await self.record_repo.get_one_by_id_with_parsing_ref_detail(mail.get("record"), object_id))[0]
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
        mail_pwd = await self.get_mail_pwd(email, db_str)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(email, mail_pwd)
            smtp_server.sendmail(email, mail.get("send_to"), mail_model.as_string())
        return "Message sent!"

    
    async def get_mail_pwd(self, email: str, db_str: str) -> str:
        result = await self.repo.find_email({"email": email, "db_str": db_str}, projection={"modified_at": 0, "created_at": 0})
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
    
    async def scan_email(self, mail: ScanMailSchema, db_str: str, current_user_id: str):
        print("START SCAN")
        # mail = mail.model_dump()
        email = mail.get("email")
        mail_pwd = await self.get_mail_pwd(email, db_str)

        template_id = mail.get("template")
        template = await self.template_repo.find_template_by_id(template_id)
        if not template:
            raise HTTPBadRequest(f"Can not find template")
        
        mail_contents = [] #List[dict]

        # bodies = MailServices.get_bodies(template.get("body"))
        with MailBox("imap.gmail.com").login(email, mail_pwd, 'INBOX') as mailbox:
            for msg in mailbox.fetch(AND(date_gte=get_current_hcm_date(), subject=r"re\*", seen=False), mark_seen=False):
                print("GOT MESS", msg.text)
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
        if len(mail_contents) != 0:
            await self.check_condition(template_id, current_user_id)
        
        return mail_contents
    

    async def check_condition(self, template_id: str, current_user_id: str):
        template = self.template_repo.find_one_by_id(template_id)
        object_id = template.get("object_id")
        workflows = await self.workflow_repo.find_many({"object_id": object_id}, {"_id": 1, "trigger": 1})
        task_ids = []
        for workflow in workflows:
            if workflow.get("trigger") != "scan":
                continue

            from Workflow.services import WorkflowService
            workflow_service = WorkflowService(self.db_str)
            # activate current workflow
            task_id = await workflow_service.activate_workflow(workflow.get("_id"), current_user_id)
            task_ids.append(task_id)

        return task_ids