import io
import csv
import email
from email import policy
import json
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import openpyxl

from apps.api.app.models.document import Document, DocumentChunk
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.services.storage_service import storage_service
from apps.api.app.services.security_scanner_service import (
    SecurityScannerService, UNTRUSTED_EXTERNAL_DATA
)
from apps.api.app.events.publisher import BusinessEventPublisher
from apps.api.app.utils.file_validator import validate_file, compute_sha256


class ParsedPage:
    def __init__(self, page_number: int, text: str, section: Optional[str] = None):
        self.page_number = page_number
        self.text = text
        self.section = section


class ParsedDocumentResult:
    def __init__(
        self,
        full_text: str,
        pages: List[ParsedPage],
        metadata: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ):
        self.full_text = full_text
        self.pages = pages
        self.metadata = metadata or {}
        self.attachments = attachments or []


class DocumentParser:
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        raise NotImplementedError

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        raise NotImplementedError


class PDFParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() == "pdf" or (mime_type and "pdf" in mime_type)

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        pages = []
        full_text_parts = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                txt = page.get_text("text").strip()
                if txt:
                    pages.append(ParsedPage(page_number=page_num + 1, text=txt))
                    full_text_parts.append(txt)
            doc.close()
        except Exception:
            # Fallback to pypdf
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                for idx, page in enumerate(reader.pages):
                    txt = page.extract_text() or ""
                    if txt.strip():
                        pages.append(ParsedPage(page_number=idx + 1, text=txt.strip()))
                        full_text_parts.append(txt.strip())
            except Exception as e:
                full_text_parts = [f"[PDF Extraction Warning: {str(e)}]"]

        full_text = "\n\n".join(full_text_parts) if full_text_parts else "[Empty PDF]"
        return ParsedDocumentResult(full_text=full_text, pages=pages)


class DOCXParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() in ["docx", "doc"]

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        paragraphs = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(content_bytes))
            for p in doc.paragraphs:
                if p.text.strip():
                    paragraphs.append(p.text.strip())
            for t in doc.tables:
                for row in t.rows:
                    row_txt = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_txt:
                        paragraphs.append(row_txt)
        except Exception:
            # Fallback basic XML inspection
            paragraphs.append("[DOCX Document Content]")

        full_text = "\n\n".join(paragraphs)
        pages = [ParsedPage(page_number=1, text=full_text)]
        return ParsedDocumentResult(full_text=full_text, pages=pages)


class XLSXParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() in ["xlsx", "xls"]

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        lines = []
        try:
            wb = openpyxl.load_workbook(io.BytesIO(content_bytes), data_only=True)
            for sheet in wb.sheetnames:
                ws = wb[sheet]
                lines.append(f"--- Sheet: {sheet} ---")
                for row in ws.iter_rows(values_only=True):
                    row_str = " | ".join(str(c) for c in row if c is not None)
                    if row_str.strip():
                        lines.append(row_str)
        except Exception as e:
            lines.append(f"[Excel Parser Error: {str(e)}]")

        full_text = "\n".join(lines)
        return ParsedDocumentResult(full_text=full_text, pages=[ParsedPage(page_number=1, text=full_text)])


class CSVParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() == "csv"

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        text_data = content_bytes.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text_data))
        lines = [" | ".join(row) for row in reader if any(row)]
        full_text = "\n".join(lines)
        return ParsedDocumentResult(full_text=full_text, pages=[ParsedPage(page_number=1, text=full_text)])


class PlainTextParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() in ["txt", "md", "markdown", "json", "log"]

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        full_text = content_bytes.decode("utf-8", errors="ignore").strip()
        return ParsedDocumentResult(full_text=full_text, pages=[ParsedPage(page_number=1, text=full_text)])


class EMLParser(DocumentParser):
    def supports(self, ext: str, mime_type: Optional[str] = None) -> bool:
        return ext.lower() in ["eml", "msg"]

    def parse(self, content_bytes: bytes) -> ParsedDocumentResult:
        msg = email.message_from_bytes(content_bytes, policy=policy.default)
        subject = msg.get("subject", "No Subject")
        sender = msg.get("from", "Unknown")
        to = msg.get("to", "Unknown")
        date = msg.get("date", "")

        body_parts = []
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))
                if "attachment" in cdispo:
                    filename = part.get_filename() or f"attachment_{len(attachments)+1}.bin"
                    payload = part.get_payload(decode=True)
                    if payload:
                        attachments.append({"filename": filename, "data": payload, "content_type": ctype})
                elif ctype == "text/plain":
                    body_parts.append(part.get_payload(decode=True).decode("utf-8", errors="ignore"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body_parts.append(payload.decode("utf-8", errors="ignore"))

        full_body = "\n".join(body_parts)
        full_text = f"Subject: {subject}\nFrom: {sender}\nTo: {to}\nDate: {date}\n\n{full_body}"
        return ParsedDocumentResult(
            full_text=full_text,
            pages=[ParsedPage(page_number=1, text=full_text)],
            metadata={"subject": subject, "sender": sender, "to": to, "date": date},
            attachments=attachments
        )


class DocumentParserRegistry:
    parsers: List[DocumentParser] = [
        PDFParser(),
        DOCXParser(),
        XLSXParser(),
        CSVParser(),
        EMLParser(),
        PlainTextParser(),
    ]

    @classmethod
    def get_parser(cls, filename: str) -> DocumentParser:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        for p in cls.parsers:
            if p.supports(ext):
                return p
        return PlainTextParser()


class DocumentIngestionService:
    """
    Multi-format Document Ingestion, Parsing, Safety Validation & Chunking Service.
    """

    @staticmethod
    def ingest_document(
        db: Session,
        organization_id: str,
        filename: str,
        content_bytes: bytes,
        uploaded_by: Optional[str] = None,
        source_type: str = "DOCUMENT",
        source_uri: Optional[str] = None,
        document_type: str = "POLICY"
    ) -> Document:
        ext, size, file_hash = validate_file(filename, content_bytes)

        # Check existing document for idempotency
        existing = db.query(Document).filter(
            Document.organization_id == organization_id,
            Document.checksum == file_hash
        ).first()
        if existing:
            return existing

        # Store raw document
        storage_key = f"documents/{organization_id}/{file_hash}.{ext}"
        storage_path = storage_service.put_object(storage_key, content_bytes)

        # Security classification and scan
        scan_res = SecurityScannerService.scan(content_bytes.decode("utf-8", errors="ignore"), UNTRUSTED_EXTERNAL_DATA)

        doc = Document(
            organization_id=organization_id,
            uploaded_by=uploaded_by,
            filename=filename,
            original_filename=filename,
            mime_type=f"application/{ext}",
            file_size=size,
            checksum=file_hash,
            storage_path=storage_path,
            storage_key=storage_key,
            document_type=document_type,
            source_type=source_type,
            source_uri=source_uri or filename,
            source_hash=file_hash,
            processing_status="PROCESSING",
            security_classification=scan_res.classification,
            security_flags=scan_res.risk_flags,
            risk_level=scan_res.risk_level
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Parse document text
        parser = DocumentParserRegistry.get_parser(filename)
        parsed_res = parser.parse(content_bytes)

        doc.raw_text = parsed_res.full_text
        doc.extracted_fields = parsed_res.metadata
        doc.processing_status = "PROCESSED"
        doc.processed_at = get_utc_now()

        # Chunk document with page numbers and source lineage for Phase 6 RAG
        DocumentIngestionService._create_chunks(db, doc, parsed_res.pages)

        db.commit()
        db.refresh(doc)

        # Emit business event
        BusinessEventPublisher.publish(
            db=db,
            organization_id=organization_id,
            event_type="DOCUMENT_PROCESSED",
            title=f"Document ingested: {filename}",
            content=parsed_res.full_text[:300],
            metadata={"document_id": doc.id, "checksum": file_hash, "chunks_count": len(doc.chunks)}
        )

        return doc

    @staticmethod
    def _create_chunks(db: Session, doc: Document, pages: List[ParsedPage]):
        chunk_idx = 0
        chunk_size = 800  # characters per chunk

        for page in pages:
            text = page.text
            if not text:
                continue
            for i in range(0, len(text), chunk_size):
                sub_text = text[i : i + chunk_size].strip()
                if not sub_text:
                    continue

                chunk = DocumentChunk(
                    organization_id=doc.organization_id,
                    document_id=doc.id,
                    chunk_index=chunk_idx,
                    content=sub_text,
                    page_number=page.page_number,
                    section=page.section,
                    token_count=len(sub_text.split()),
                    chunk_metadata={
                        "source_type": doc.source_type,
                        "source_uri": doc.source_uri,
                        "source_hash": doc.source_hash,
                        "filename": doc.filename,
                        "ingested_at": doc.created_at.isoformat() if doc.created_at else None
                    }
                )
                db.add(chunk)
                chunk_idx += 1
