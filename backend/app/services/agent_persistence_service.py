import json
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from backend.app.models import Workflow, AgentLog, Document
from backend.app.schemas.agent import AgentInput, AgentOutput, AgentStatus


def persist_agent_results(
    db: Session,
    agent_input: AgentInput,
    results: dict[str, AgentOutput],
) -> Workflow:
    """
    Save workflow, agent execution logs, and generated documents.

    All database changes are committed in one transaction.
    """

    try:
        # 1. Retrieve an existing workflow or create a new one.
        if agent_input.workflow_id is not None:
            workflow = db.get(Workflow, agent_input.workflow_id)

            if workflow is None:
                raise ValueError(
                    f"Workflow with ID {agent_input.workflow_id} not found."
                )

            workflow.status = "RUNNING"

        else:
            workflow = Workflow(
                title=agent_input.task[:255],
                description=agent_input.task,
                status="RUNNING",
                source_type=agent_input.source_type,
                source_reference=agent_input.source_reference,
            )

            db.add(workflow)
            db.flush()

        # 2. Prepare workflow input summary.
        input_summary = json.dumps(
            {
                "task": agent_input.task,
                "source_type": agent_input.source_type,
                "source_reference": agent_input.source_reference,
            }
        )

        completed_count = 0
        failed_count = 0

        # 3. Save each agent's execution record.
        for result in results.values():

            completed_at = datetime.now(timezone.utc)

            execution_time_ms = result.execution_time_ms or 0

            started_at = completed_at - timedelta(
                milliseconds=execution_time_ms
            )

            if result.status == AgentStatus.COMPLETED:
                completed_count += 1
            else:
                failed_count += 1

            agent_log = AgentLog(
                workflow_id=workflow.id,
                agent_name=result.agent_name.value,
                status=result.status.value,
                input_summary=input_summary,
                output_summary=(
                    json.dumps(result.result)
                    if result.result is not None
                    else None
                ),
                error_message=result.error,
                started_at=started_at,
                completed_at=completed_at,
            )

            db.add(agent_log)

            # 4. Save generated Markdown documentation.
            if (
                result.status == AgentStatus.COMPLETED
                and result.result
                and result.agent_name.value == "documentation"
            ):
                markdown = result.result.get("generated_markdown")

                if markdown:
                    document = Document(
                        workflow_id=workflow.id,
                        title=f"{workflow.title} - Documentation",
                        document_type="MARKDOWN",
                        content=markdown,
                    )

                    db.add(document)

        # 5. Determine final workflow status.
        total_agents = len(results)
        if total_agents == 0 or failed_count == total_agents:
            workflow.status = "FAILED"
        elif failed_count > 0:
            workflow.status = "PARTIAL"
        else:
            # Ensure newly created documents are available for querying.
            db.flush()
            # Retrieve all documents belonging to this workflow.
            documents = (
                db.query(Document)
                .filter(Document.workflow_id == workflow.id)
                .all()
            )
            approval_statuses = [
                document.approval_status
                for document in documents
            ]
            if not approval_statuses:
                workflow.status = "COMPLETED"
            elif "PENDING" in approval_statuses:
                workflow.status = "AWAITING_APPROVAL"
            elif "REJECTED" in approval_statuses:
                workflow.status = "REJECTED"
            elif all(
                approval_status == "APPROVED"
                for approval_status in approval_statuses
            ):
                workflow.status = "APPROVED"
            else:
                workflow.status = "COMPLETED"

        # 6. Commit all changes together.
        db.commit()
        db.refresh(workflow)

        return workflow

    except Exception:
        db.rollback()
        raise