"""
Phase 19: UrbanThread Fashion & Clothing Catalog RAG Knowledge Ingestion.
Extracts all clothing products, sizing guides, fabric specifications, and e-commerce SOPs,
chunks them into semantic passages, computes dense vector embeddings, and stores them in
KnowledgeDocument & KnowledgeChunk for grounded AI retrieval.
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization
from apps.api.app.models.ecommerce import Product, ProductCategory, ProductVariant, Inventory
from apps.api.app.models.knowledge import KnowledgeDocument, KnowledgeChunk
from apps.api.app.services.knowledge_service import KnowledgeService, simple_text_embedding


FASHION_SOP_DOCUMENTS = [
    {
        "title": "UrbanThread Master Apparel Sizing & Fit Guide",
        "category": "SIZING_GUIDE",
        "content": """URBANTHREAD MASTER APPAREL SIZING & FIT GUIDE — 2026 EDITION

1. MEN'S APPAREL SIZING MATRIX (INCHES):
- Size XS (36): Chest 34-36", Waist 28-30", Shoulder 16.5", Length 26.5"
- Size S  (38): Chest 37-39", Waist 30-32", Shoulder 17.5", Length 27.5"
- Size M  (40): Chest 40-42", Waist 32-34", Shoulder 18.5", Length 28.5"
- Size L  (42): Chest 43-45", Waist 35-37", Shoulder 19.5", Length 29.5"
- Size XL (44): Chest 46-48", Waist 38-40", Shoulder 20.5", Length 30.5"
- Size XXL(46): Chest 49-51", Waist 41-43", Shoulder 21.5", Length 31.5"

2. WOMEN'S APPAREL SIZING MATRIX (INCHES):
- Size XS (UK 6):  Bust 31-33", Waist 24-26", Hips 34-36", Length (Midi) 46"
- Size S  (UK 8):  Bust 33-35", Waist 26-28", Hips 36-38", Length (Midi) 47"
- Size M  (UK 10): Bust 35-37", Waist 28-30", Hips 38-40", Length (Midi) 48"
- Size L  (UK 12): Bust 38-40", Waist 31-33", Hips 41-43", Length (Midi) 49"
- Size XL (UK 14): Bust 41-43", Waist 34-36", Hips 44-46", Length (Midi) 50"

3. FIT PROFILES & RECOMMENDATIONS:
- Boxy & Oversized Fit (e.g., UT-TSH-003, UT-HOD-001): Designed with dropped shoulders and a wider chest. If you prefer a regular tailored look, order one size down.
- Relaxed Linen Fit (e.g., UT-SHR-001): True to size with a breezy drape.
- Japanese Selvedge Denim (e.g., UT-JNS-001): Rigid 13.5 oz denim with zero elastane. Measure true waist. Denim relaxes ~0.5 inches after 10-15 wears.
- Bodycon & Wrap Dresses (e.g., UT-DRS-002, UT-DRS-003): True to size with flexible wrap ties."""
    },
    {
        "title": "UrbanThread Fabric Science & Garment Care Handbook",
        "category": "FABRIC_CARE",
        "content": """URBANTHREAD FABRIC SCIENCE & GARMENT CARE DIRECTIVE

1. 100% GOTS ORGANIC COMBED COTTON (240 GSM):
- Properties: Ring-spun long-staple cotton, hypoallergenic, ultra-soft with double-needle ribbed collar.
- Washing: Machine wash cold (below 30°C) with mild eco-friendly liquid detergent.
- Drying: Air dry in shade. Avoid high-heat tumble drying to prevent shrinking. Iron medium heat.

2. 100% EUROPEAN FLAX LINEN:
- Properties: Sourced from Normandy flax, highly breathable, natural antimicrobial moisture wicking.
- Washing: Gentle cold machine wash or hand wash. Do not wring or twist.
- Ironing: Iron while slightly damp or steam on high heat for a crisp tailored aesthetic.

3. JAPANESE RAW SELVEDGE DENIM (13.5 OZ):
- Properties: Shuttle-loom woven in Kojima, red-line selvedge ID, unwashed indigo dyed.
- Washing: Wear raw for 4-6 months before first wash to set natural whiskers and honeycombs. Wash inside out in cold water with woolite dark. Never machine dry.

4. VEGAN MULBERRY SILK & RAYON BLENDS:
- Properties: Fluid evening drape, cruelty-free satin finish.
- Washing: Dry clean or delicate hand wash with silk-safe ph-neutral wash. Hang dry on padded hanger."""
    },
    {
        "title": "UrbanThread Storefront Shipping, Return & Exchange Policy",
        "category": "STORE_POLICY",
        "content": """URBANTHREAD STOREFRONT POLICIES — REVERSE LOGISTICS & DISPATCH

1. SHIPPING & DELIVERY TIMELINES:
- Tier 1 Metro Cities (Mumbai, Delhi-NCR, Bangalore, Hyderabad, Chennai, Kolkata): 2 to 3 business days via BlueDart Air.
- Tier 2 & 3 Cities: 4 to 6 business days via Delhivery Express.
- Free Express Delivery across India on all prepaid and COD orders exceeding ₹1,499.

2. RETURN & EXCHANGE WINDOW:
- 14 calendar days from the exact delivery timestamp logged by courier partner.
- Eligible conditions: garment must be unworn, unwashed, free of stains/perfumes, with all tags and security barcodes intact.
- Items marked 'Final Clearance Sale' are non-refundable.

3. REVERSE PICKUP PROCESS:
- Free automated reverse pickup scheduled within 24 hours of customer request.
- Courier partner generates return shipping label; driver inspects tags on doorstep pickup.

4. REFUND PROCESSING SPEED:
- Instant Store Credit: 100% refund value credited immediately upon courier scan with +5% bonus credit.
- Original Payment Method (UPI / Credit Card / NetBanking): Initiated within 2 hours of warehouse QC check, credited in 2-3 business days."""
    }
]


def seed_clothing_rag(db=None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # Find UrbanThread organization
        org = db.query(Organization).filter(Organization.slug == "urbanthread").first()
        if not org:
            org = db.query(Organization).first()

        if not org:
            print("Error: No organization found to seed RAG knowledge.")
            return

        print("=" * 60)
        print("OpsPilot — Ingesting & Training Clothing RAG Knowledge Store")
        print(f"Organization: {org.name} ({org.id})")
        print("=" * 60)

        seeded_docs = 0
        seeded_chunks = 0

        # 1. Ingest Master Sizing, Fabric, and Store SOPs
        for sop in FASHION_SOP_DOCUMENTS:
            existing = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.organization_id == org.id,
                KnowledgeDocument.title == sop["title"]
            ).first()

            if existing:
                db.delete(existing)
                db.commit()

            doc = KnowledgeService.index_document(
                organization_id=org.id,
                title=sop["title"],
                category=sop["category"],
                content=sop["content"].strip(),
                db=db
            )
            seeded_docs += 1
            seeded_chunks += len(doc.chunks)
            print(f"✓ Indexed SOP: {doc.title} ({len(doc.chunks)} chunks embedded)")

        # 2. Ingest every catalog product into RAG
        products = db.query(Product).filter(
            Product.organization_id == org.id,
            Product.is_active == True
        ).all()

        print(f"\nProcessing {len(products)} clothing products into RAG vector knowledge...")
        for p in products:
            doc_title = f"Product Spec: {p.name} ({p.sku})"

            # Remove previous version if any
            existing = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.organization_id == org.id,
                KnowledgeDocument.title == doc_title
            ).first()
            if existing:
                db.delete(existing)
                db.commit()

            cat_name = p.category.name if p.category else "Apparel"
            variants_str = ", ".join(sorted(list(set(v.size for v in p.variants)))) if p.variants else "S, M, L, XL"
            colors_str = p.color or (p.variants[0].color if p.variants else "Standard")

            content = f"""PRODUCT SPECIFICATION SHEET
Title: {p.name}
SKU: {p.sku}
Brand: {p.brand}
Category: {cat_name}
Target Gender: {p.gender}
Base Price: ₹{p.base_price}
Sale / Offer Price: ₹{p.sale_price or p.base_price}
Material Composition: {p.material or '100% Cotton'}
Color Options: {colors_str}
Available Sizing: {variants_str}
Description: {p.description or 'Handcrafted contemporary apparel tailored for modern versatility.'}
Care Instructions: {p.care_instructions or 'Machine wash cold on gentle cycle, tumble dry low or hang dry in shade.'}
Store Guarantee: 14-day return and exchange window. 100% authentic UrbanThread garment.
Stock Status: In stock and ready for express courier dispatch from Mumbai/Bangalore fulfillment hubs."""

            doc = KnowledgeService.index_document(
                organization_id=org.id,
                title=doc_title,
                category="PRODUCT",
                content=content.strip(),
                db=db
            )
            seeded_docs += 1
            seeded_chunks += len(doc.chunks)

        print("=" * 60)
        print(f"RAG TRAINING COMPLETE! {seeded_docs} Documents Indexed, {seeded_chunks} Total Vector Chunks Embedded.")
        print("=" * 60)

    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_clothing_rag()
