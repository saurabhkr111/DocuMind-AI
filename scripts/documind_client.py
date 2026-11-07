"""
DocuMind AI - Integration Client

Provides a Python interface to the existing FastAPI backend.
Uses standard Python libraries only.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from typing import Any, Optional


# ============================================================
# CUSTOM API ERROR
# ============================================================

class DocuMindAPIError(Exception):
    """Raised when the DocuMind API returns an error."""


# ============================================================
# DOCUMIND API CLIENT
# ============================================================

class DocuMindClient:

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        api_key: Optional[str] = None,
        timeout: int = 60,
    ):

        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.getenv("DOCU_MIND_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "DOCU_MIND_API_KEY environment variable "
                "is not configured."
            )

    # --------------------------------------------------------
    # COMMON HTTP REQUEST HANDLER
    # --------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict] = None,
    ) -> Any:

        url = f"{self.base_url}{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        data = None

        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method=method,
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:

                response_data = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

                if not response_data:
                    return None

                return json.loads(response_data)

        except urllib.error.HTTPError as exc:

            error_body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise DocuMindAPIError(
                f"HTTP {exc.code}: {error_body}"
            ) from exc

        except urllib.error.URLError as exc:

            raise DocuMindAPIError(
                f"Cannot connect to DocuMind backend: {exc.reason}"
            ) from exc

        except TimeoutError as exc:

            raise DocuMindAPIError(
                "Request timed out."
            ) from exc

    # --------------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------------

    def health_check(self):

        return self._request(
            "GET",
            "/health",
        )

    # --------------------------------------------------------
    # PROJECT INFORMATION
    # --------------------------------------------------------

    def project_info(self):

        return self._request(
            "GET",
            "/api/v1/info",
        )

    # --------------------------------------------------------
    # CREATE WORKFLOW
    # --------------------------------------------------------

    def create_workflow(
        self,
        title: str,
        description: Optional[str] = None,
        source_type: Optional[str] = "manual",
        source_reference: Optional[str] = None,
    ):

        payload = {
            "title": title,
            "description": description,
            "source_type": source_type,
            "source_reference": source_reference,
        }

        return self._request(
            "POST",
            "/api/v1/workflows/",
            payload,
        )

    # --------------------------------------------------------
    # RUN THREE AI AGENTS
    # --------------------------------------------------------

    def run_agents(
        self,
        task: str,
        workflow_id: Optional[int] = None,
        source_type: Optional[str] = "manual",
        source_reference: Optional[str] = None,
        context: Optional[dict] = None,
    ):

        payload = {
            "task": task,
            "workflow_id": workflow_id,
            "source_type": source_type,
            "source_reference": source_reference,
            "context": context or {},
        }

        return self._request(
            "POST",
            "/api/v1/agents/analyze",
            payload,
        )

    # --------------------------------------------------------
    # GET WORKFLOW
    # --------------------------------------------------------

    def get_workflow(self, workflow_id: int):

        return self._request(
            "GET",
            f"/api/v1/workflows/{workflow_id}",
        )

    # --------------------------------------------------------
    # GET WORKFLOW DETAILS
    # --------------------------------------------------------

    def get_workflow_details(self, workflow_id: int):

        return self._request(
            "GET",
            f"/api/v1/workflows/{workflow_id}/details",
        )

    # --------------------------------------------------------
    # GET ALL WORKFLOWS
    # --------------------------------------------------------

    def get_all_workflows(self):

        return self._request(
            "GET",
            "/api/v1/workflows/",
        )

    # --------------------------------------------------------
    # GET DOCUMENT
    # --------------------------------------------------------

    def get_document(self, document_id: int):

        return self._request(
            "GET",
            f"/api/v1/documents/{document_id}",
        )

    # --------------------------------------------------------
    # APPROVE DOCUMENT
    # --------------------------------------------------------

    def approve_document(self, document_id: int):

        return self._request(
            "POST",
            f"/api/v1/documents/{document_id}/approve",
            {},
        )

    # --------------------------------------------------------
    # REJECT DOCUMENT
    # --------------------------------------------------------

    def reject_document(
        self,
        document_id: int,
        reason: str,
    ):

        if len(reason.strip()) < 5:
            raise ValueError(
                "Rejection reason must contain at least 5 characters."
            )

        return self._request(
            "POST",
            f"/api/v1/documents/{document_id}/reject",
            {"reason": reason},
        )


# ============================================================
# JSON CONTEXT LOADER
# ============================================================

def load_context(context_json=None, context_file=None):
    """
    Load repository context from either a JSON string
    or a JSON file.

    UTF-8-SIG supports files with and without a BOM.
    """

    context = {}

    if context_json:

        try:
            context = json.loads(context_json)

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Invalid JSON passed through --context-json: {exc}"
            ) from exc

    elif context_file:

        try:

            with open(
                context_file,
                "r",
                encoding="utf-8-sig",
            ) as file:

                context = json.load(file)

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Invalid JSON in context file: {exc}"
            ) from exc

        except OSError as exc:

            raise ValueError(
                f"Cannot read context file '{context_file}': {exc}"
            ) from exc

    if not isinstance(context, dict):

        raise ValueError(
            "Context must be a JSON object."
        )

    return context


# ============================================================
# PRINT API RESULT
# ============================================================

def print_result(result):

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False,
            default=str,
        )
    )


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="DocuMind AI Integration Client"
    )

    parser.add_argument(
        "--base-url",
        default=os.getenv(
            "DOCU_MIND_BASE_URL",
            "http://127.0.0.1:8001",
        ),
        help="DocuMind backend URL.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    subparsers.add_parser(
        "health",
        help="Check backend health.",
    )

    # --------------------------------------------------------
    # INFO
    # --------------------------------------------------------

    subparsers.add_parser(
        "info",
        help="Get project information.",
    )

    # --------------------------------------------------------
    # WORKFLOWS
    # --------------------------------------------------------

    subparsers.add_parser(
        "workflows",
        help="List all workflows.",
    )

    # --------------------------------------------------------
    # CREATE WORKFLOW
    # --------------------------------------------------------

    create_parser = subparsers.add_parser(
        "create",
        help="Create a new workflow.",
    )

    create_parser.add_argument(
        "--title",
        required=True,
    )

    create_parser.add_argument(
        "--description",
    )

    create_parser.add_argument(
        "--source-type",
        default="manual",
    )

    create_parser.add_argument(
        "--source-reference",
    )

    # --------------------------------------------------------
    # RUN AGENTS
    # --------------------------------------------------------

    run_parser = subparsers.add_parser(
        "run",
        help="Execute the three-agent workflow.",
    )

    run_parser.add_argument(
        "--task",
        required=True,
    )

    run_parser.add_argument(
        "--workflow-id",
        type=int,
    )

    run_parser.add_argument(
        "--source-type",
        default="manual",
    )

    run_parser.add_argument(
        "--source-reference",
    )

    context_group = run_parser.add_mutually_exclusive_group()

    context_group.add_argument(
        "--context-json",
        help="Repository context as a JSON object.",
    )

    context_group.add_argument(
        "--context-file",
        help="Path to a JSON file containing repository context.",
    )

    # --------------------------------------------------------
    # WORKFLOW DETAILS
    # --------------------------------------------------------

    details_parser = subparsers.add_parser(
        "details",
        help="Get workflow details and agent logs.",
    )

    details_parser.add_argument(
        "--workflow-id",
        type=int,
        required=True,
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    document_parser = subparsers.add_parser(
        "document",
        help="Get a generated document.",
    )

    document_parser.add_argument(
        "--document-id",
        type=int,
        required=True,
    )

    # --------------------------------------------------------
    # APPROVE
    # --------------------------------------------------------

    approve_parser = subparsers.add_parser(
        "approve",
        help="Approve a generated document.",
    )

    approve_parser.add_argument(
        "--document-id",
        type=int,
        required=True,
    )

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    reject_parser = subparsers.add_parser(
        "reject",
        help="Reject a generated document.",
    )

    reject_parser.add_argument(
        "--document-id",
        type=int,
        required=True,
    )

    reject_parser.add_argument(
        "--reason",
        required=True,
    )

    # --------------------------------------------------------
    # PARSE ARGUMENTS
    # --------------------------------------------------------

    args = parser.parse_args()

    try:

        client = DocuMindClient(
            base_url=args.base_url,
        )

        # HEALTH
        if args.command == "health":

            result = client.health_check()

        # INFO
        elif args.command == "info":

            result = client.project_info()

        # ALL WORKFLOWS
        elif args.command == "workflows":

            result = client.get_all_workflows()

        # CREATE
        elif args.command == "create":

            result = client.create_workflow(
                title=args.title,
                description=args.description,
                source_type=args.source_type,
                source_reference=args.source_reference,
            )

        # RUN AGENTS
        elif args.command == "run":

            context = load_context(
                context_json=args.context_json,
                context_file=args.context_file,
            )

            result = client.run_agents(
                task=args.task,
                workflow_id=args.workflow_id,
                source_type=args.source_type,
                source_reference=args.source_reference,
                context=context,
            )

        # WORKFLOW DETAILS
        elif args.command == "details":

            result = client.get_workflow_details(
                args.workflow_id,
            )

        # GET DOCUMENT
        elif args.command == "document":

            result = client.get_document(
                args.document_id,
            )

        # APPROVE DOCUMENT
        elif args.command == "approve":

            result = client.approve_document(
                args.document_id,
            )

        # REJECT DOCUMENT
        elif args.command == "reject":

            result = client.reject_document(
                args.document_id,
                args.reason,
            )

        else:

            raise ValueError(
                f"Unsupported command: {args.command}"
            )

        print_result(result)

    except (
        DocuMindAPIError,
        ValueError,
    ) as exc:

        print(
            f"\nERROR: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()