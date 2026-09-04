import pytest
from apps.api.app.models import Organization, User, Document, Invoice


def test_tenant_isolation(db_session):
    acme_org = db_session.query(Organization).filter_by(slug="acme-test").first()
    beta_org = db_session.query(Organization).filter_by(slug="beta-test").first()

    assert acme_org is not None
    assert beta_org is not None
    assert acme_org.id != beta_org.id

    # Create document for Acme
    doc_acme = Document(
        organization_id=acme_org.id,
        file_name="acme_confidential_q1.pdf",
        file_type="pdf",
        file_size=1024,
        file_hash="hash_acme_123",
        storage_path="/storage/acme.pdf",
        status="PROCESSED"
    )
    db_session.add(doc_acme)

    # Create document for Beta
    doc_beta = Document(
        organization_id=beta_org.id,
        file_name="beta_internal_board.pdf",
        file_type="pdf",
        file_size=2048,
        file_hash="hash_beta_456",
        storage_path="/storage/beta.pdf",
        status="PROCESSED"
    )
    db_session.add(doc_beta)
    db_session.commit()

    # Query scoped to Acme organization
    acme_docs = db_session.query(Document).filter(Document.organization_id == acme_org.id).all()
    acme_doc_names = [d.file_name for d in acme_docs]
    assert "acme_confidential_q1.pdf" in acme_doc_names
    assert "beta_internal_board.pdf" not in acme_doc_names

    # Query scoped to Beta organization
    beta_docs = db_session.query(Document).filter(Document.organization_id == beta_org.id).all()
    beta_doc_names = [d.file_name for d in beta_docs]
    assert "beta_internal_board.pdf" in beta_doc_names
    assert "acme_confidential_q1.pdf" not in beta_doc_names
