from typing import Optional

from pydantic import BaseModel, Field


class ResumeExtractionField(BaseModel):
    value: str = ''
    status: str = 'pending_confirmation'
    confidence: float = 0.0
    source_excerpt: str = ''
    reason: str = ''


class ResumePendingField(BaseModel):
    field_path: str
    label: str
    reason: str


class ResumeSkillItem(BaseModel):
    canonical_name: str
    category: str
    matched_alias: str = ''
    confidence: float = 0.0
    source_excerpt: str = ''


class ResumeStructuredSkills(BaseModel):
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    matched_skills: list[ResumeSkillItem] = Field(default_factory=list)
    unmatched_candidates: list[str] = Field(default_factory=list)


class ResumeExperienceItem(BaseModel):
    item_type: str
    title: str = ''
    organization: str = ''
    role: str = ''
    time_range: str = ''
    description: str = ''
    tech_stack: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    pending_fields: list[str] = Field(default_factory=list)
    source_excerpt: str = ''


class ResumeCertificateItem(BaseModel):
    name: str
    obtained_at: str = ''
    confidence: float = 0.0
    source_excerpt: str = ''
    pending_fields: list[str] = Field(default_factory=list)


class ResumeInnovationIndicators(BaseModel):
    has_awards: bool = False
    has_patents: bool = False
    has_publications: bool = False
    has_entrepreneurship: bool = False
    award_items: list[str] = Field(default_factory=list)
    patent_items: list[str] = Field(default_factory=list)
    publication_items: list[str] = Field(default_factory=list)
    entrepreneurship_items: list[str] = Field(default_factory=list)


class ResumeBasicInfo(BaseModel):
    name: ResumeExtractionField = Field(default_factory=ResumeExtractionField)
    school: ResumeExtractionField = Field(default_factory=ResumeExtractionField)
    major: ResumeExtractionField = Field(default_factory=ResumeExtractionField)
    degree: ResumeExtractionField = Field(default_factory=ResumeExtractionField)
    graduation_year: ResumeExtractionField = Field(default_factory=ResumeExtractionField)


class ResumeFormFillSuggestion(BaseModel):
    name: str = ''
    school: str = ''
    major: str = ''
    degree: str = ''
    graduation_year: Optional[int] = None
    manual_skills: list[str] = Field(default_factory=list)
    project_experiences: list[str] = Field(default_factory=list)
    internship_experiences: list[str] = Field(default_factory=list)
    campus_experiences: list[str] = Field(default_factory=list)
    certificates: list[str] = Field(default_factory=list)
    self_description: str = ''
    pending_prompts: list[str] = Field(default_factory=list)


class ResumeStructuredProfile(BaseModel):
    basic_info: ResumeBasicInfo = Field(default_factory=ResumeBasicInfo)
    skills: ResumeStructuredSkills = Field(default_factory=ResumeStructuredSkills)
    project_experiences: list[ResumeExperienceItem] = Field(default_factory=list)
    internship_experiences: list[ResumeExperienceItem] = Field(default_factory=list)
    campus_experiences: list[ResumeExperienceItem] = Field(default_factory=list)
    certificates: list[ResumeCertificateItem] = Field(default_factory=list)
    innovation_indicators: ResumeInnovationIndicators = Field(default_factory=ResumeInnovationIndicators)
    pending_fields: list[ResumePendingField] = Field(default_factory=list)
    extraction_notes: list[str] = Field(default_factory=list)
    form_fill_suggestion: ResumeFormFillSuggestion = Field(default_factory=ResumeFormFillSuggestion)


class ResumeParseResponse(BaseModel):
    file_name: str
    file_type: str
    parsed_success: bool
    extracted_text: str
    preview: str
    char_count: int
    section_hints: list[str] = Field(default_factory=list)
    message: str = ''
    structured_profile: Optional[ResumeStructuredProfile] = None
    form_fill_suggestion: Optional[ResumeFormFillSuggestion] = None
