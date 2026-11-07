import asyncio

from backend.app.agents.documentation_agent import DocumentationAgent
from backend.app.schemas.agent import AgentInput

async def main():
    agent = DocumentationAgent()

    agent_input = AgentInput(
        task="Analyze GitHub pull request changes",
        source_type="github_pull_request",
        context={
            "repository": "fastapi/fastapi",
            "commits": [
                {"message": "Improve websocket test client lifecycle"}
            ],
            "changed_files": [
                {
                    "filename": "tests/test_websockets.py",
                    "status": "modified",
                    "patch": """@@ -1,5 +1,4 @@
 import pytest
-time.sleep(0.01)
+with TestClient(app) as client:
+    yield client
"""
                }
            ]
        }
    )

    output = await agent.run(agent_input)

    print("STATUS:", output.status)

    if output.result:
        print("\nSUMMARY:")
        print(output.result["summary"])

        print("\nGENERATED MARKDOWN:")
        print(output.result["generated_markdown"])

        print("\nFILES COVERED:")
        print(output.result["files_covered"])

        print("\nDOCUMENTATION GAPS:")
        print(output.result["documentation_gaps"])

    else:
        print("ERROR:", output.error)

asyncio.run(main())
