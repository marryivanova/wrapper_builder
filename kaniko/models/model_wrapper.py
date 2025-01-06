import typing as t

from pydantic.v1 import BaseModel, Field


class BuildArgs(BaseModel):
    key: str
    value: str


class ServiceData(BaseModel):
    image: t.Optional[str] = None
    build: t.Optional[t.Dict[str, t.Any]] = None

    class Config:
        extra = "ignore"

    def __init__(self, **data):
        super().__init__(**data)
        if self.build is None:
            self.build = {}


class DockerComposeFile(BaseModel):
    services: t.Dict[str, ServiceData]

    class Config:
        extra = "ignore"


class CommandLineOptions(BaseModel):
    compose_file: str = Field(default="docker-compose.yml")
    kaniko_image: str = Field(default="gcr.io/kaniko-project/executor:latest")
    deploy: bool = Field(default=False)
    dry_run: bool = Field(default=False)

    class Config:
        extra = "ignore"
