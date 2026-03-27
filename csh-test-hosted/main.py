from azure.ai.agentserver.core import FoundryCBAgent, AgentRunContext
from azure.ai.agentserver.core.models.projects._models import (
    Response,
    ResponsesAssistantMessageItemResource,
    ItemContentOutputText,
)

class TestAgent(FoundryCBAgent):
    def agent_run(self, context: AgentRunContext) -> Response:
        return Response(
            id=context.response_id,
            status="completed",
            output=[
                ResponsesAssistantMessageItemResource(
                    id=f"msg_{context.response_id}",
                    type="message",
                    role="assistant",
                    content=[ItemContentOutputText(text="Hello from hosted agent!", type="output_text", annotations=[])],
                    status="completed",
                )
            ],
        )

if __name__ == "__main__":
    TestAgent().run()
