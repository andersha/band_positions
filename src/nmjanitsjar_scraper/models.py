"""
Data models for Norwegian Wind Band Orchestra competition data.

These Pydantic models define the structure of competition results including
orchestras, divisions, placements, and awards.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Placement(BaseModel):
    """Represents a single orchestra's placement in a division."""
    
    rank: Optional[int] = Field(None, description="Placement rank (1st, 2nd, etc.)")
    orchestra: str = Field(..., description="Orchestra name")
    pieces: List[str] = Field(default_factory=list, description="Musical pieces performed")
    points: Optional[float] = Field(None, description="Points scored (max 100)")
    conductor: Optional[str] = Field(None, description="Conductor name")
    orchestra_url: Optional[str] = Field(None, description="Link to orchestra page")
    conductor_url: Optional[str] = Field(None, description="Link to conductor page")
    piece_urls: List[str] = Field(default_factory=list, description="Links to piece pages")
    image_url: Optional[str] = Field(None, description="Orchestra image URL")
    
    @validator('orchestra')
    def normalize_orchestra_name(cls, v):
        """Normalize orchestra name by stripping whitespace and fixing casing."""
        return v.strip() if v else None
    
    @validator('conductor')
    def normalize_conductor_name(cls, v):
        """Normalize conductor name by stripping whitespace."""
        return v.strip() if v else None
    
    @validator('points')
    def validate_points(cls, v):
        """Ensure points are within reasonable range."""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Points must be between 0 and 100")
        return v


class Award(BaseModel):
    """Represents an award (best soloist or best group) within a division."""
    
    award_type: str = Field(..., description="Type of award (soloist/group)")
    recipient: str = Field(..., description="Award recipient name")
    orchestra: Optional[str] = Field(None, description="Associated orchestra")


class Division(BaseModel):
    """Represents a competition division with its placements and awards."""
    
    name: str = Field(..., description="Division name (Elite, 1., 2., etc.)")
    placements: List[Placement] = Field(default_factory=list, description="Orchestra placements")
    awards: List[Award] = Field(default_factory=list, description="Division awards")
    
    @validator('name')
    def normalize_division_name(cls, v):
        """Normalize division name."""
        return v.strip() if v else None


class CompetitionYear(BaseModel):
    """Represents a complete year's competition results."""
    
    year: int = Field(..., description="Competition year")
    divisions: List[Division] = Field(default_factory=list, description="All divisions")
    total_orchestras: Optional[int] = Field(None, description="Total number of participating orchestras")
    location: Optional[str] = Field(None, description="Competition location")
    date: Optional[str] = Field(None, description="Competition date")
    source_url: Optional[str] = Field(None, description="Source URL")
    scraped_at: datetime = Field(default_factory=datetime.now, description="Timestamp when data was scraped")
    
    @validator('year')
    def validate_year(cls, v):
        """Ensure year is within expected range."""
        if v < 1981 or v > 2030:
            raise ValueError("Year must be between 1981 and 2030")
        return v
    
    def get_total_orchestras(self) -> int:
        """Calculate total number of orchestras across all divisions."""
        return sum(len(division.placements) for division in self.divisions)
    
    def get_division_by_name(self, name: str) -> Optional[Division]:
        """Get a specific division by name."""
        for division in self.divisions:
            if division.name.lower() == name.lower():
                return division
        return None


class ScrapingMetadata(BaseModel):
    """Metadata about the scraping process."""
    
    total_years: int = Field(..., description="Total years attempted to scrape")
    successful_years: List[int] = Field(default_factory=list, description="Successfully scraped years")
    failed_years: List[int] = Field(default_factory=list, description="Failed years")
    total_orchestras: int = Field(default=0, description="Total orchestras scraped")
    total_divisions: int = Field(default=0, description="Total divisions scraped")
    scraping_started: datetime = Field(default_factory=datetime.now)
    scraping_completed: Optional[datetime] = Field(None)
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors encountered")
