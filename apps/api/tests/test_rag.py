import pytest
from apps.api.app.services.knowledge_service import KnowledgeService
from apps.api.app.models import Organization


def test_rag_index_and_search(db_session):
    org = db_session.query(Organization).filter_by(slug="acme-test").first()

    sop_text = (
        "Standard Operating Procedure: All vendor invoices exceeding INR 100,000 "
        "require mandatory approval from the Finance Manager before payment disbursement. "
        "Invoices under INR 50,000 may be auto-processed if matched with an approved Purchase Order."
    )

    doc = KnowledgeService.index_document(
        organization_id=org.id,
        title="Finance SOP FIN-001",
        category="FINANCE_POLICY",
        content=sop_text,
        db=db_session
    )
    assert doc.id is not None

    # Search for approval threshold
    results = KnowledgeService.search(org.id, "invoice exceeding 100000 approval", top_k=1, db=db_session)
    assert len(results) > 0
    assert "Finance SOP FIN-001" in results[0]["document_title"]

    # Grounded Q&A
    ans = KnowledgeService.answer_policy_question(org.id, "Does an invoice above 100000 require approval?", db=db_session)
    assert ans["policy_found"] is True
    assert "Finance SOP FIN-001" in ans["source"]

    # Unknown policy check
    unknown = KnowledgeService.answer_policy_question(org.id, "extraterrestrial moon space travel expense policy", db=db_session)
    assert unknown["policy_found"] is False
    assert "Policy not found" in unknown["answer"]
