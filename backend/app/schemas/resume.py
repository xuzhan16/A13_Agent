from pydantic import BaseModel, Field


class ResumeParseResponse(BaseModel):
    file_name: str
    file_type: str
    parsed_success: bool
    extracted_text: str
    preview: str
    char_count: int
    section_hints: list[str] = Field(default_factory=list)
    message: str = ''
