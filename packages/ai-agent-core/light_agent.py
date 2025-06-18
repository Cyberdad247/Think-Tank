import time
from typing import Callable

class LightAgent:
    """
    A simplified "LightAgent" equivalent with a basic TAL engine for single-round reasoning.
    It does not perform complex multi-round reasoning or actual LLM calls.
    """
    def __init__(self, publish_progress: Callable[[str, str], None]):
        self.publish_progress = publish_progress

    def run_reasoning(self, persona_prompt: str, query: str) -> str:
        """
        Performs a simplified single-round reasoning process.
        Publishes mock progress updates.
        """
        task_id = "mock_task_" + str(int(time.time())) # Generate a unique ID for mock progress updates

        self.publish_progress(task_id, "Starting single-round reasoning...")
        time.sleep(0.1) # Simulate some work

        # Simplified TAL engine: concatenation or mock debate
        reasoning_output = f"LightAgent's simplified reasoning output:\n" \
                           f"Persona Context: {persona_prompt}\n" \
                           f"User Query: {query}\n" \
                           f"Mock Debate Result: 'After a brief internal deliberation, the LightAgent concludes that the most efficient approach is to combine the provided persona guidance with the user's direct request, leading to a focused and pragmatic initial response.'"

        self.publish_progress(task_id, "Reasoning complete. Generating response...")
        time.sleep(0.1) # Simulate some more work

        self.publish_progress(task_id, f"Final response generated.")
        return reasoning_output