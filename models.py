from typing import Literal

from pydantic import BaseModel, Field


class VendorDecision(BaseModel):
    """Structured answer the agent returns for one vendor document."""

    vendor: str = Field(description="Vendor name exactly as the document gives it.")
    sku: str | None = Field(description="Campus Customs SKU (e.g. CC-HD-006); null if the document has none.")
    unit_price: float | None = Field(description="Quoted price per unit in USD; null if not stated.")
    lead_time_days: int | None = Field(description="Lead time as a number of days; null if not stated.")
    min_order: int | None = Field(description="Minimum order in units; null if not stated.")
    decision: Literal["recommend", "do_not_recommend"] = Field(
        description="recommend only if all four handbook checks pass."
    )
    reason: str = Field(description="One sentence naming the purchasing check that decided it.")


class ExtractedFacts(BaseModel):
    """Facts read from a vendor document. Used by the design layer: the model only extracts, code decides."""

    vendor: str = Field(description="Vendor name exactly as the document gives it.")
    sku: str | None = Field(description="Campus Customs SKU; null if the document has none.")
    unit_price: float | None = Field(description="Quoted price per unit in USD; null if not stated.")
    lead_time_days: int | None = Field(description="Lead time as a number of days; null if not stated.")
    min_order: int | None = Field(description="Minimum order in units; null if not stated.")
