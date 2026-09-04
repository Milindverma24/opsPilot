import io
import csv
import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from apps.api.app.models.document import ImportJob
from apps.api.app.models.base import get_utc_now
from apps.api.app.models.operations import Customer, Vendor
from apps.api.app.services.product_service import ProductService
from apps.api.app.services.inventory_service import InventoryService
from apps.api.app.events.publisher import BusinessEventPublisher
from apps.api.app.models.audit import AuditLog


class ImportService:
    """
    Business Data Batch Import Engine.
    Processes CSV / JSON datasets for customers, products, inventory, orders, and vendors
    with per-row validation, tenant enforcement, and detailed error reports.
    """

    @staticmethod
    def create_import_job(
        db: Session,
        organization_id: str,
        entity_type: str,
        filename: str,
        source_type: str = "CSV"
    ) -> ImportJob:
        valid_entities = {"customers", "products", "inventory", "orders", "vendors", "purchase_orders"}
        if entity_type.lower() not in valid_entities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported entity type '{entity_type}'. Allowed: {sorted(list(valid_entities))}"
            )

        job = ImportJob(
            organization_id=organization_id,
            source_type=source_type.upper(),
            entity_type=entity_type.lower(),
            filename=filename,
            status="PENDING",
            total_records=0,
            successful_records=0,
            failed_records=0,
            error_report=[]
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def process_import_job(
        db: Session,
        job_id: str,
        organization_id: str,
        content_bytes: bytes
    ) -> ImportJob:
        job = db.query(ImportJob).filter(
            ImportJob.id == job_id,
            ImportJob.organization_id == organization_id
        ).first()

        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found.")

        job.status = "PROCESSING"
        job.started_at = get_utc_now()
        db.commit()

        # Parse records from CSV or JSON
        records: List[Dict[str, Any]] = []
        try:
            if job.source_type == "JSON":
                parsed = json.loads(content_bytes.decode("utf-8", errors="ignore"))
                records = parsed if isinstance(parsed, list) else [parsed]
            else:
                text_stream = io.StringIO(content_bytes.decode("utf-8", errors="ignore"))
                reader = csv.DictReader(text_stream)
                records = [row for row in reader if any(row.values())]
        except Exception as e:
            job.status = "FAILED"
            job.error_report = [{"error": f"File parsing failed: {str(e)}"}]
            job.completed_at = get_utc_now()
            db.commit()
            return job

        job.total_records = len(records)
        success_count = 0
        fail_count = 0
        errors = []

        for idx, row in enumerate(records):
            row_num = idx + 1
            try:
                if job.entity_type == "customers":
                    ImportService._import_customer(db, organization_id, row)
                elif job.entity_type == "products":
                    ImportService._import_product(db, organization_id, row)
                elif job.entity_type == "vendors":
                    ImportService._import_vendor(db, organization_id, row)
                else:
                    raise ValueError(f"Entity handler for '{job.entity_type}' is not configured.")
                success_count += 1
            except Exception as row_err:
                fail_count += 1
                errors.append({"row": row_num, "error": str(row_err), "data": row})

        job.successful_records = success_count
        job.failed_records = fail_count
        job.error_report = errors
        job.completed_at = get_utc_now()

        if fail_count == 0:
            job.status = "COMPLETED"
        elif success_count > 0:
            job.status = "PARTIALLY_COMPLETED"
        else:
            job.status = "FAILED"

        db.commit()
        db.refresh(job)

        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="DATA_IMPORT_COMPLETED",
            title=f"Import {job.filename} finished ({job.status})",
            content=f"Processed {len(records)} records. Success: {success_count}, Failed: {fail_count}.",
            metadata={"job_id": job.id, "entity_type": job.entity_type, "status": job.status}
        )

        return job

    @staticmethod
    def _import_customer(db: Session, organization_id: str, row: Dict[str, Any]):
        email = row.get("email", "").strip()
        name = row.get("name", "").strip()
        if not email or not name:
            raise ValueError("Customer row requires 'name' and 'email'.")

        existing = db.query(Customer).filter(
            Customer.organization_id == organization_id,
            Customer.email == email
        ).first()

        if not existing:
            cust = Customer(
                organization_id=organization_id,
                name=name,
                email=email,
                phone=row.get("phone", "").strip() or None,
                status=row.get("status", "ACTIVE").upper()
            )
            db.add(cust)
            db.commit()

    @staticmethod
    def _import_product(db: Session, organization_id: str, row: Dict[str, Any]):
        sku = row.get("sku", "").strip()
        name = row.get("name", "").strip()
        base_price_str = row.get("base_price", "0")
        if not sku or not name:
            raise ValueError("Product row requires 'sku' and 'name'.")

        base_price = float(base_price_str)
        sale_price = float(row["sale_price"]) if row.get("sale_price") else None

        ProductService.create_product(
            db=db,
            organization_id=organization_id,
            sku=sku,
            name=name,
            base_price=base_price,
            sale_price=sale_price,
            brand=row.get("brand", "UrbanThread"),
            gender=row.get("gender", "UNISEX").upper()
        )

    @staticmethod
    def _import_vendor(db: Session, organization_id: str, row: Dict[str, Any]):
        name = row.get("name", "").strip()
        code = row.get("code", row.get("vendor_code", "")).strip()
        if not name:
            raise ValueError("Vendor row requires 'name'.")

        existing = db.query(Vendor).filter(
            Vendor.organization_id == organization_id,
            Vendor.name == name
        ).first()

        if not existing:
            vendor = Vendor(
                organization_id=organization_id,
                vendor_code=code or None,
                name=name,
                email=row.get("email", "").strip() or None,
                phone=row.get("phone", "").strip() or None,
                status=row.get("status", "ACTIVE").upper()
            )
            db.add(vendor)
            db.commit()
