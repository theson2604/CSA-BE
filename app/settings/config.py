from pydantic import BaseModel, ValidationError
import yaml
import os

with open('app/configs/env.yml', 'r') as file:
    # Load the YAML data
    config = yaml.safe_load(file)

class ServerConfiguration(BaseModel):
    PROJECT_NAME: str = "CSA_BACKEND"
    ALLOWED_HOSTS: str = "127.0.0.1"
    VERSION: str = "v1.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    WORKERS: int = 1
    PREFIX: str = "/api"
    DOCS_ROUTE: str = "/docs"
    RE_DOC_ROUTE: str = "/redoc"
    
class MongoConfiguration(BaseModel):
    MONGO_URI: str # Required
    MONGO_HOST: str = "127.0.0.1"
    MONGO_PORT: str = "27017"
    MONGO_UESR: str = None
    MONGO_PASSWORD: str = None
    MONGO_PATH: str = None

try:
    ServerConfig = ServerConfiguration(**config)
    MongoConfig = MongoConfiguration(**config)
    SECRET_SALT = config.get("SECRET_SALT")
    JWT_ALGORITHM = config.get("JWT_ALGORITHM")
    ROOT_DIR = config.get("ROOT_DIR")
    ELASTIC_HOST = config.get("ELASTIC_HOST")
    ELASTIC_USERNAME = config.get("ELASTIC_USERNAME")
    ELASTIC_PASSWORD = config.get("ELASTIC_PASSWORD")
    
    KEY_BYTES = config.get("KEY_BYTES")
except ValidationError as e:
    print(e)