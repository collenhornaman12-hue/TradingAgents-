from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import (
    build_instrument_context,
    get_language_instruction,
    get_arxiv_papers,
    get_arxiv_finance_papers,
)


def create_arxiv_analyst(llm):
    def arxiv_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = build_instrument_context(state["company_of_interest"])

        tools = [
            get_arxiv_papers,
            get_arxiv_finance_papers,
        ]

        system_message = (
            "You are an academic research analyst specializing in quantitative finance and economics. "
            "Your task is to search arXiv for recent academic papers that are relevant to the company or "
            "instrument being analyzed and the broader financial and economic environment. "
            "Use get_arxiv_papers() to search for company-specific, sector-specific, or technology research. "
            "Use get_arxiv_finance_papers() to find relevant quantitative finance and macroeconomic studies. "
            "Synthesize the key findings from these papers into actionable trading insights: what does current "
            "academic research say about valuation methods, risk factors, market dynamics, or AI/ML trends "
            "relevant to this instrument? Look for papers on topics such as earnings predictability, sector "
            "momentum, interest rate sensitivity, volatility regimes, or any domain-specific factors that may "
            "affect the instrument. Highlight any papers with direct implications for the trading decision and "
            "explain how the academic evidence should inform the investment thesis."
            + " Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. {instrument_context}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(instrument_context=instrument_context)

        chain = prompt | llm.bind_tools(tools)
        result = chain.invoke(state["messages"])

        report = ""
        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "arxiv_report": report,
        }

    return arxiv_analyst_node
