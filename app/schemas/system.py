from pydantic import BaseModel


class SystemInfo(BaseModel):
    name: str
    version: str
    environment: str
    api_prefix: str
