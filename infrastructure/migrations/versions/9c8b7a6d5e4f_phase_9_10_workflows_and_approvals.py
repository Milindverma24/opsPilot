"""phase_9_10_workflows_and_approvals

Revision ID: 9c8b7a6d5e4f
Revises: 785a8c89f7e2
Create Date: 2026-09-04 07:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '9c8b7a6d5e4f'
down_revision: Union[str, Sequence[str], None] = '785a8c89f7e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema for Phase 9 & 10 with existence checks."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()

    # 1. Update workflows table
    wf_cols = [c['name'] for c in inspector.get_columns('workflows')] if 'workflows' in tables else []
    with op.batch_alter_table('workflows', schema=None) as batch_op:
        if 'name' not in wf_cols:
            batch_op.add_column(sa.Column('name', sa.String(length=200), nullable=False, server_default='Operational Workflow'))
        if 'description' not in wf_cols:
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if 'trigger_type' not in wf_cols:
            batch_op.add_column(sa.Column('trigger_type', sa.String(length=50), nullable=False, server_default='BUSINESS_EVENT'))
        if 'enabled' not in wf_cols:
            batch_op.add_column(sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'))
        if 'version' not in wf_cols:
            batch_op.add_column(sa.Column('version', sa.String(length=20), nullable=False, server_default='v1'))
        if 'configuration' not in wf_cols:
            batch_op.add_column(sa.Column('configuration', sa.JSON(), nullable=False, server_default='{}'))
        if 'max_concurrent_runs' not in wf_cols:
            batch_op.add_column(sa.Column('max_concurrent_runs', sa.Integer(), nullable=False, server_default='10'))
        if 'timeout_seconds' not in wf_cols:
            batch_op.add_column(sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='3600'))

    # 2. Update workflow_steps table
    wfs_cols = [c['name'] for c in inspector.get_columns('workflow_steps')] if 'workflow_steps' in tables else []
    with op.batch_alter_table('workflow_steps', schema=None) as batch_op:
        if 'organization_id' not in wfs_cols:
            batch_op.add_column(sa.Column('organization_id', sa.String(length=36), nullable=True))
        if 'name' not in wfs_cols:
            batch_op.add_column(sa.Column('name', sa.String(length=200), nullable=False, server_default='Workflow Step'))
        if 'description' not in wfs_cols:
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if 'configuration' not in wfs_cols:
            batch_op.add_column(sa.Column('configuration', sa.JSON(), nullable=False, server_default='{}'))
        if 'timeout_seconds' not in wfs_cols:
            batch_op.add_column(sa.Column('timeout_seconds', sa.Integer(), nullable=False, server_default='300'))
        if 'max_retries' not in wfs_cols:
            batch_op.add_column(sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'))
        if 'retry_backoff_seconds' not in wfs_cols:
            batch_op.add_column(sa.Column('retry_backoff_seconds', sa.Integer(), nullable=False, server_default='5'))
        if 'continue_on_failure' not in wfs_cols:
            batch_op.add_column(sa.Column('continue_on_failure', sa.Boolean(), nullable=False, server_default='0'))

    # 3. Create workflow_runs table if missing
    if 'workflow_runs' not in tables:
        op.create_table(
            'workflow_runs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('workflow_id', sa.String(length=36), nullable=False),
            sa.Column('agent_run_id', sa.String(length=36), nullable=True),
            sa.Column('trigger_event_id', sa.String(length=36), nullable=True),
            sa.Column('idempotency_key', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('current_step_id', sa.String(length=36), nullable=True),
            sa.Column('current_step_order', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('input_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('context_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('decision_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('execution_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('error_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('paused_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('failed_at', sa.DateTime(), nullable=True),
            sa.Column('next_run_at', sa.DateTime(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_workflow_runs_organization_id', 'workflow_runs', ['organization_id'], unique=False)
        op.create_index('ix_workflow_runs_workflow_id', 'workflow_runs', ['workflow_id'], unique=False)
        op.create_index('ix_workflow_runs_agent_run_id', 'workflow_runs', ['agent_run_id'], unique=False)
        op.create_index('ix_workflow_runs_trigger_event_id', 'workflow_runs', ['trigger_event_id'], unique=False)
        op.create_index('ix_workflow_runs_idempotency_key', 'workflow_runs', ['idempotency_key'], unique=False)
        op.create_index('ix_workflow_runs_status', 'workflow_runs', ['status'], unique=False)

    # 4. Create workflow_step_runs table if missing
    if 'workflow_step_runs' not in tables:
        op.create_table(
            'workflow_step_runs',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('workflow_run_id', sa.String(length=36), nullable=False),
            sa.Column('workflow_step_id', sa.String(length=36), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
            sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('input_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('output_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('decision_data', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('tool_execution_id', sa.String(length=36), nullable=True),
            sa.Column('approval_id', sa.String(length=36), nullable=True),
            sa.Column('error_code', sa.String(length=100), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('next_retry_at', sa.DateTime(), nullable=True),
            sa.Column('duration_ms', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workflow_run_id'], ['workflow_runs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workflow_step_id'], ['workflow_steps.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tool_execution_id'], ['tool_executions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_workflow_step_runs_organization_id', 'workflow_step_runs', ['organization_id'], unique=False)
        op.create_index('ix_workflow_step_runs_workflow_run_id', 'workflow_step_runs', ['workflow_run_id'], unique=False)
        op.create_index('ix_workflow_step_runs_workflow_step_id', 'workflow_step_runs', ['workflow_step_id'], unique=False)
        op.create_index('ix_workflow_step_runs_status', 'workflow_step_runs', ['status'], unique=False)

    # 5. Update approvals table
    appr_cols = [c['name'] for c in inspector.get_columns('approvals')] if 'approvals' in tables else []
    with op.batch_alter_table('approvals', schema=None) as batch_op:
        if 'workflow_run_id' not in appr_cols:
            batch_op.add_column(sa.Column('workflow_run_id', sa.String(length=36), nullable=True))
        if 'workflow_step_run_id' not in appr_cols:
            batch_op.add_column(sa.Column('workflow_step_run_id', sa.String(length=36), nullable=True))
        if 'agent_run_id' not in appr_cols:
            batch_op.add_column(sa.Column('agent_run_id', sa.String(length=36), nullable=True))
        if 'tool_execution_id' not in appr_cols:
            batch_op.add_column(sa.Column('tool_execution_id', sa.String(length=36), nullable=True))
        if 'requested_by_type' not in appr_cols:
            batch_op.add_column(sa.Column('requested_by_type', sa.String(length=50), nullable=False, server_default='AI_EMPLOYEE'))
        if 'requested_by_id' not in appr_cols:
            batch_op.add_column(sa.Column('requested_by_id', sa.String(length=36), nullable=True))
        if 'approval_type' not in appr_cols:
            batch_op.add_column(sa.Column('approval_type', sa.String(length=50), nullable=False, server_default='HIGH_RISK_OPERATION'))
        if 'title' not in appr_cols:
            batch_op.add_column(sa.Column('title', sa.String(length=255), nullable=False, server_default='Action Approval Request'))
        if 'description' not in appr_cols:
            batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        if 'action_type' not in appr_cols:
            batch_op.add_column(sa.Column('action_type', sa.String(length=100), nullable=True))
        if 'action_payload' not in appr_cols:
            batch_op.add_column(sa.Column('action_payload', sa.JSON(), nullable=False, server_default='{}'))
        if 'action_payload_hash' not in appr_cols:
            batch_op.add_column(sa.Column('action_payload_hash', sa.String(length=64), nullable=True))
        if 'policy_snapshot' not in appr_cols:
            batch_op.add_column(sa.Column('policy_snapshot', sa.JSON(), nullable=False, server_default='{}'))
        if 'risk_snapshot' not in appr_cols:
            batch_op.add_column(sa.Column('risk_snapshot', sa.JSON(), nullable=False, server_default='{}'))
        if 'approval_mode' not in appr_cols:
            batch_op.add_column(sa.Column('approval_mode', sa.String(length=50), nullable=False, server_default='ONE_APPROVER'))
        if 'required_roles' not in appr_cols:
            batch_op.add_column(sa.Column('required_roles', sa.JSON(), nullable=False, server_default='["MANAGER"]'))
        if 'approvals_received' not in appr_cols:
            batch_op.add_column(sa.Column('approvals_received', sa.JSON(), nullable=False, server_default='[]'))
        if 'expires_at' not in appr_cols:
            batch_op.add_column(sa.Column('expires_at', sa.DateTime(), nullable=True))
        if 'rejected_by' not in appr_cols:
            batch_op.add_column(sa.Column('rejected_by', sa.String(length=36), nullable=True))
        if 'cancelled_at' not in appr_cols:
            batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        if 'metadata' not in appr_cols:
            batch_op.add_column(sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'))

    # 6. Create approval_comments table if missing
    if 'approval_comments' not in tables:
        op.create_table(
            'approval_comments',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('approval_id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('user_id', sa.String(length=36), nullable=True),
            sa.Column('comment', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['approval_id'], ['approvals.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_approval_comments_approval_id', 'approval_comments', ['approval_id'], unique=False)
        op.create_index('ix_approval_comments_organization_id', 'approval_comments', ['organization_id'], unique=False)

    # 7. Create escalations table if missing
    if 'escalations' not in tables:
        op.create_table(
            'escalations',
            sa.Column('id', sa.String(length=36), nullable=False),
            sa.Column('organization_id', sa.String(length=36), nullable=False),
            sa.Column('workflow_run_id', sa.String(length=36), nullable=True),
            sa.Column('agent_run_id', sa.String(length=36), nullable=True),
            sa.Column('approval_id', sa.String(length=36), nullable=True),
            sa.Column('level', sa.String(length=50), nullable=False, server_default='LEVEL_1'),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False, server_default='HIGH'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='OPEN'),
            sa.Column('assigned_to', sa.String(length=36), nullable=True),
            sa.Column('assigned_team', sa.String(length=100), nullable=True),
            sa.Column('due_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolution', sa.Text(), nullable=True),
            sa.Column('dedup_key', sa.String(length=255), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workflow_run_id'], ['workflow_runs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['agent_run_id'], ['agent_runs.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['approval_id'], ['approvals.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_escalations_organization_id', 'escalations', ['organization_id'], unique=False)
        op.create_index('ix_escalations_workflow_run_id', 'escalations', ['workflow_run_id'], unique=False)
        op.create_index('ix_escalations_level', 'escalations', ['level'], unique=False)
        op.create_index('ix_escalations_severity', 'escalations', ['severity'], unique=False)
        op.create_index('ix_escalations_status', 'escalations', ['status'], unique=False)
        op.create_index('ix_escalations_due_at', 'escalations', ['due_at'], unique=False)
        op.create_index('ix_escalations_dedup_key', 'escalations', ['dedup_key'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    pass
