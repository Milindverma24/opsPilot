from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LineItemSchema(BaseModel):
    description: str = Field(description="Item description or service name")
    quantity: float = Field(default=1.0, description="Quantity billed")
    unit_price: float = Field(description="Price per single unit")
    tax: float = Field(default=0.0, description="Tax calculated on this item")
    total: float = Field(description="Line total: quantity * unit_price + tax")


class InvoiceExtractionResult(BaseModel):
    invoice_number: Optional[str] = Field(default=None, description="Invoice or bill identifier")
    vendor_name: Optional[str] = Field(default=None, description="Legal company or trade name of the supplier")
    vendor_tax_id: Optional[str] = Field(default=None, description="GSTIN, VAT, or Tax Identification Number")
    invoice_date: Optional[str] = Field(default=None, description="Date of issuance (YYYY-MM-DD)")
    due_date: Optional[str] = Field(default=None, description="Payment due date (YYYY-MM-DD)")
    currency: str = Field(default="INR", description="Three-letter ISO currency code, e.g. INR, USD, EUR")
    subtotal: float = Field(default=0.0, description="Net amount before tax")
    tax: float = Field(default=0.0, description="Total tax or GST amount")
    total: float = Field(default=0.0, description="Final gross amount payable")
    purchase_order_number: Optional[str] = Field(default=None, description="Associated Purchase Order (PO) number")
    payment_terms: Optional[str] = Field(default=None, description="e.g. Net 30, Immediate, Due on receipt")
    bank_details: Dict[str, Any] = Field(default_factory=dict, description="Bank name, account number, IFSC/SWIFT")
    line_items: List[LineItemSchema] = Field(default_factory=list, description="Extracted individual itemized rows")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="Extraction confidence score")


class InvoiceValidationResult(BaseModel):
    is_valid: bool = Field(default=True, description="Whether mathematical and structural checks passed")
    math_valid: bool = Field(default=True, description="Whether subtotal + tax roughly equals total")
    calculated_subtotal: float = Field(default=0.0)
    calculated_tax: float = Field(default=0.0)
    calculated_total: float = Field(default=0.0)
    errors: List[str] = Field(default_factory=list, description="Hard validation failures")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings (e.g. missing bank details)")
    po_matched: bool = Field(default=False, description="Whether PO number exists and matches in database")
    po_amount_variance_percent: float = Field(default=0.0, description="Variance between PO and invoice amount")
    is_duplicate: bool = Field(default=False, description="Whether this invoice number already exists for this vendor")
