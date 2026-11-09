from typing import Optional, Literal
from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    chemical_name: list[str] = Field(default_factory=list)
    cas_number: list[str] = Field(default_factory=list)
    company_name: list[str] = Field(default_factory=list)
    brand_name: list[str] = Field(default_factory=list)
    product_name: list[str] = Field(default_factory=list)


class ExtractedFilters(BaseModel):
    primary_category: Optional[str] = None
    subcategory: Optional[str] = None

    initial_date_from: Optional[str] = None
    initial_date_to: Optional[str] = None

    discontinued_date_from: Optional[str] = None
    discontinued_date_to: Optional[str] = None

    lifecycle_status: Optional[
        Literal["active", "discontinued", "removed"]
    ] = None


class EntityExtractionOutput(BaseModel):
    intent: Literal[
        "lookup",
        "list",
        "compare",
        "summarize",
        "trend_analysis",
        "data_quality"
    ]

    entities: ExtractedEntities
    filters: ExtractedFilters