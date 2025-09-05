"""
Multi-Agent Orchestrator:
Central coordinator for routing queries to specialist agents.
Uses AI for intent classification and manages workflows.
"""

import asyncio
from openai import AsyncOpenAI  # For OpenRouter API calls
from shared.mcp_connector import MCPConnector  # Placeholder; implement later
from agents.investment_advisor import InvestmentAdvisor  # Placeholder

class MultiAgentOrchestrator:
    def __init__(self, llm_provider='openrouter', api_key='your-openrouter-api-key'):
        self.mcp = MCPConnector()  # Initialize MCP bridge
        self.advisor = InvestmentAdvisor()  # Initialize advisor agent
        # Add more agents in Phase 2
        
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.llm_client = None
        self._init_llm_client()

    def _init_llm_client(self):
        if self.llm_provider == 'openrouter':
            self.llm_client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key
            )
        elif self.llm_provider == 'gemini':
            # Optional: Vertex AI init (uncomment if switching)
            # from google.cloud import aiplatform
            # aiplatform.init(project='your-project-id')
            # self.llm_client = aiplatform.TextGenerationModel.from_pretrained('text-bison')
            pass
        else:
            raise ValueError("Unsupported LLM provider")

    async def classify_intent(self, query):
        if self.llm_provider == 'openrouter' and self.llm_client:
            try:
                response = await self.llm_client.chat.completions.create(
                    model="gpt-4o-mini",  # Or your preferred model (e.g., 'meta-llama/llama-3.1-8b-instruct')
                    messages=[
                        {"role": "system", "content": "Classify the intent of this query for a finance agent system. Possible intents: investment_advice, market_analysis, expense_tracking, portfolio_management, or unknown."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=50,
                    temperature=0.3
                )
                intent = response.choices[0].message.content.strip().lower()
                return intent
            except Exception as e:
                print(f"Error in LLM call: {e}")
                return "unknown"
        # Add handling for other providers here
        return "investment_advice"  # Fallback

    async def route_query(self, query):
        intent = await self.classify_intent(query)
        if intent == "investment_advice":
            return await self.advisor.process_query(query)
        # Add routes for other intents/agents in Phase 2
        return f"Query routed for {intent}"  # Placeholder response

# Entry point for testing (optional, remove if not needed)
async def main():
    orch = MultiAgentOrchestrator(llm_provider='openrouter', api_key='your-openrouter-api-key')
    result = await orch.route_query("Analyze my portfolio performance")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
