from typing import List, Optional
from pydantic import BaseModel, Field


class ExtractedPropertyDetails(BaseModel):
    """
    Structured Pydantic model for holding extracted property details from raw user text.
    """
    property_type: Optional[str] = Field(
        default=None,
        description="The type of property (e.g. Apartment, Villa, Townhouse, Condominium, Land)."
    )
    location: Optional[str] = Field(
        default=None,
        description="The geographical location, address, neighborhood, or city of the property."
    )
    area: Optional[str] = Field(
        default=None,
        description="The area or physical size of the property (e.g., '120 sqm', '2500 sqft', '10x20m')."
    )
    price: Optional[str] = Field(
        default=None,
        description="The listing price, pricing terms, or rental/purchase cost mentioned."
    )
    legal_status: Optional[str] = Field(
        default=None,
        description="Legal document status (e.g., 'Red Book', 'Pink Book', 'SPA signed', 'LURC')."
    )
    amenities: Optional[str] = Field(
        default=None,
        description="Amenities or features mentioned (e.g., 'Pool, Gym, Balcony, Parking')."
    )
    financial_policy: Optional[str] = Field(
        default=None,
        description="Financial policies (e.g., '70% loan support', '0% interest for 12 months', '10% down payment')."
    )
    target_customer: Optional[str] = Field(
        default=None,
        description="Primary target customer persona or buyer demographic mentioned (e.g., 'young family looking for home', 'rental investor')."
    )
    marketing_goal: Optional[str] = Field(
        default=None,
        description="Marketing or business objective of the post if mentioned (e.g., 'quick sale', 'brand trust', 'inbox generation')."
    )

