from pydantic import BaseModel, Field, ConfigDict

class Token(BaseModel): token: str; role: str; username: str
class Login(BaseModel): username: str; password: str
class ShowIn(BaseModel): title: str; slug: str; synopsis: str = ""; section: str | None = None; categories: list[str] = []; status: str = "draft"
class ShowOut(ShowIn): id: int; model_config = ConfigDict(from_attributes=True)
class SeasonIn(BaseModel): show_id: int; season_number: int = Field(ge=0); title: str = ""
class SeasonOut(SeasonIn): id: int; model_config = ConfigDict(from_attributes=True)
class EpisodeIn(BaseModel):
    season_id: int; episode_id: str; episode_number: int = Field(ge=1); title: str; duration_seconds: int | None = Field(default=None, ge=1); language: str; content_group: str; categories: list[str] = []; synopsis: str = ""; status: str = "draft"
class EpisodeOut(EpisodeIn): id: int; artwork_available: list[str] = []; model_config = ConfigDict(from_attributes=True)
