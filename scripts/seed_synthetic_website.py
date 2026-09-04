import hashlib
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from apps.api.app.models.tenant import Organization
from apps.api.app.models.website import Website, WebsitePage
from apps.api.app.models.base import get_utc_now
from apps.api.app.services.storage_service import storage_service
from apps.api.app.services.security_scanner_service import SecurityScannerService, UNTRUSTED_EXTERNAL_DATA

SYNTHETIC_PAGES: List[Dict[str, Any]] = [
    {
        "url": "https://urbanthread.local/",
        "title": "UrbanThread | Sustainable Contemporary Apparel",
        "meta_desc": "Consciously crafted apparel made from 100% Indian organic cotton. Free shipping across India on orders over ₹1,500.",
        "content": """UrbanThread — Contemporary Sustainable Apparel.
Crafted with precision, designed for everyday ease. 
Our collections include oversized cotton tees, tailored linen shirts, selvedge denim, and breezy midi dresses.
Every garment is ethically spun and dyed in Mumbai, Bangalore, and Surat."""
    },
    {
        "url": "https://urbanthread.local/products",
        "title": "All Collections | UrbanThread",
        "meta_desc": "Explore our complete range of premium shirts, t-shirts, jeans, and dresses.",
        "content": """Explore UrbanThread Collections.
Men: Oversized T-Shirts (240 GSM), Linen Work Shirts, Selvedge Denim (13.5 oz).
Women: Organic Cotton Midi Dresses, Relaxed Fit Denim, Linen Everyday Shirts.
Accessories: Canvas Utility Tote Bags, Washed Twill Caps, Leather Belts."""
    },
    {
        "url": "https://urbanthread.local/products/tshirts",
        "title": "Organic Cotton T-Shirts | UrbanThread",
        "meta_desc": "Heavyweight 240 GSM organic cotton t-shirts in earth tones.",
        "content": """UrbanThread T-Shirt Range.
Material: 100% GOTS-Certified Organic Indian Cotton.
Fabric Weight: 240 GSM Heavyweight Terry.
Available Sizes: XS, S, M, L, XL.
Care: Cold machine wash inside out. Do not tumble dry. Iron on low reverse."""
    },
    {
        "url": "https://urbanthread.local/products/jeans",
        "title": "Selvedge & Relaxed Denim | UrbanThread",
        "meta_desc": "Raw and washed selvedge denim woven on vintage shuttle looms.",
        "content": """UrbanThread Selvedge Denim.
Weave: 13.5 oz Right-Hand Twill with Red Selvedge ID line.
Fit Options: Classic Straight Fit, Relaxed Tapered Fit.
Colorways: Raw Indigo, Stone Washed Light Indigo, Carbon Black."""
    },
    {
        "url": "https://urbanthread.local/products/dresses",
        "title": "Linen & Cotton Midi Dresses | UrbanThread",
        "meta_desc": "Effortless silhouette dresses made from breathable natural linen.",
        "content": """UrbanThread Women's Dresses.
Fabrics: 100% French Flax Linen and Breathable Cotton Poplin.
Styles: Tiered Smock Dress, Belted Wrap Dress, Sleeveless Trapeze Dress.
Features: Deep concealed side pockets, biodegradable horn buttons."""
    },
    {
        "url": "https://urbanthread.local/shipping",
        "title": "Shipping Policy & Domestic Logistics | UrbanThread",
        "meta_desc": "Delivery timeframes, courier partners, and free shipping terms.",
        "content": """UrbanThread Shipping Policy.
Domestic Delivery Timeframes:
- Metro Cities (Mumbai, Bangalore, Delhi NCR, Chennai): 2 to 3 business days.
- Non-Metro & Tier 2/3 Towns: 4 to 7 business days.
Shipping Rates:
- Orders ₹1,500 and above: FREE standard delivery.
- Orders below ₹1,500: Flat ₹100 delivery fee across India.
Courier Partners: BlueDart, Delhivery, ExpressLogistics."""
    },
    {
        "url": "https://urbanthread.local/returns",
        "title": "Returns & Exchange Policy | UrbanThread",
        "meta_desc": "14-day hassle-free returns on unworn clothing items with original tags intact.",
        "content": """UrbanThread Return & Exchange Policy.
Return Window: Customers have 14 calendar days from the recorded delivery timestamp to request a return or size exchange.
Eligibility Criteria:
1. Items must be unworn, unwashed, and in their original packaging.
2. All original product tags, barcodes, and security seals must be intact.
3. Intimates, socks, and face coverings are non-returnable for hygiene reasons.
Return Pickup: Free reverse pickup arranged at your delivery address."""
    },
    {
        "url": "https://urbanthread.local/refunds",
        "title": "Refund Disbursement Guidelines | UrbanThread",
        "meta_desc": "Refund timeline and settlement methods across UPI, Cards, and NetBanking.",
        "content": """UrbanThread Refund Guidelines.
Inspection & Processing: Once returned items arrive at our regional warehouse, our quality control team completes inspection within 48 hours.
Disbursement Timelines:
- UPI Payments: Credited back to source account within 24 hours of approval.
- Credit / Debit Cards: Settled in 3 to 5 business days depending on the issuing bank.
- Net Banking: 3 to 5 business days.
- Cash on Delivery (COD): Transferred via NEFT/IMPS to customer's verified bank account."""
    },
    {
        "url": "https://urbanthread.local/faq",
        "title": "Frequently Asked Questions | UrbanThread",
        "meta_desc": "Common questions about sizing, payments, order tracking, and returns.",
        "content": """UrbanThread FAQ.
Q: How do I choose my size?
A: Our sizing runs true to modern tailored fit. We recommend referring to the garment measurement table on each product page.
Q: Can I change my delivery address after placing an order?
A: Address edits are supported before the order status reaches 'SHIPPED'. Contact support immediately.
Q: How do I track my delivery?
A: Use your BD-URB tracking number on our tracking portal or BlueDart tracking website."""
    },
    {
        "url": "https://urbanthread.local/contact",
        "title": "Contact Customer Support | UrbanThread",
        "meta_desc": "Reach our Bangalore operations team via email, WhatsApp, or phone.",
        "content": """Contact UrbanThread Support.
Customer Care Email: support@urbanthread.local
Corporate Headquarters: UrbanThread Retail Private Limited, 4th Floor, Indiranagar 100ft Road, Bangalore, Karnataka 560038, India.
Support Hours: Monday to Saturday, 9:00 AM - 7:00 PM IST.
Emergency Operations Escalations: operations@urbanthread.local"""
    },
    {
        "url": "https://urbanthread.local/about",
        "title": "About UrbanThread | Our Story & Ethics",
        "meta_desc": "How UrbanThread is building a circular, sustainable fashion movement in India.",
        "content": """About UrbanThread.
Founded in 2024, UrbanThread was born out of a desire for enduring style without environmental compromise.
We partner directly with organic cotton farmers in Gujarat and handloom weavers in Karnataka.
Zero single-use plastics in our fulfillment supply chain."""
    },
    {
        "url": "https://urbanthread.local/terms",
        "title": "Terms of Service | UrbanThread",
        "meta_desc": "Legal terms governing your purchase and use of UrbanThread platforms.",
        "content": """UrbanThread Terms of Service.
All purchases are governed by Indian contract laws and subject to jurisdiction in Bangalore, Karnataka.
Prices are inclusive of 12% Goods and Services Tax (GST).
Promotional discount codes are subject to specific validity dates and cart minimums."""
    },
    {
        "url": "https://urbanthread.local/privacy",
        "title": "Privacy & Data Protection Notice | UrbanThread",
        "meta_desc": "How we collect, store, and safeguard your personal data.",
        "content": """UrbanThread Privacy Policy.
We respect customer privacy and adhere to the Digital Personal Data Protection (DPDP) Act.
Payment credentials are processed exclusively via PCI-DSS certified gateways and never stored on our servers.
Customer browsing behavior is not sold to third-party ad brokers."""
    }
]


def seed_synthetic_urbanthread_website(db: Session, org_id: str):
    site = db.query(Website).filter(
        Website.organization_id == org_id,
        Website.url == "https://urbanthread.local"
    ).first()

    if not site:
        site = Website(
            organization_id=org_id,
            name="UrbanThread Official Storefront",
            url="https://urbanthread.local",
            description="Primary e-commerce storefront for catalog, shipping, and return policies",
            allowed_domains=["urbanthread.local"],
            respect_robots_txt=True,
            max_depth=3,
            max_pages=50,
            status="ACTIVE",
            crawl_status="COMPLETED",
            last_crawled_at=get_utc_now()
        )
        db.add(site)
        db.commit()
        db.refresh(site)

    for page_data in SYNTHETIC_PAGES:
        url = page_data["url"]
        content = page_data["content"].strip()
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        storage_key = f"websites/{site.id}/{c_hash}.html"

        # Write raw content to local storage
        storage_service.put_object(storage_key, content.encode("utf-8"), "text/html")

        scan_res = SecurityScannerService.scan(content, UNTRUSTED_EXTERNAL_DATA)

        page = db.query(WebsitePage).filter(
            WebsitePage.website_id == site.id,
            WebsitePage.url == url
        ).first()

        if not page:
            page = WebsitePage(
                website_id=site.id,
                organization_id=org_id,
                url=url,
                canonical_url=url,
                title=page_data["title"],
                content=content,
                raw_content_reference=storage_key,
                content_hash=c_hash,
                http_status=200,
                content_type="text/html",
                language="en",
                meta_description=page_data["meta_desc"],
                crawl_status="COMPLETED",
                security_classification=scan_res.classification,
                security_flags=scan_res.risk_flags,
                first_seen_at=get_utc_now(),
                last_crawled_at=get_utc_now()
            )
            db.add(page)
        else:
            page.title = page_data["title"]
            page.content = content
            page.content_hash = c_hash
            page.last_crawled_at = get_utc_now()

    db.commit()
    print(f"✓ Seeded {len(SYNTHETIC_PAGES)} synthetic website pages for UrbanThread.")
