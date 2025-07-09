from langchain.tools.retriever import create_retriever_tool
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from typing import List, TypedDict, Dict, Any, Annotated
import json

from agent.vectorstore import LANGCHAIN_VECTOR_STORES
from config import CONFIG
from utils import log
import agent.prompts as prompts

class AgentState(TypedDict):
    """
    State management for the agentic RAG workflow.
    
    Attributes:
        messages: Sequence of messages in the conversation
        question_rewrite_count: Number of times the question has been rewritten
        processing_log: List of log messages for debugging
        next_workflow_node: The next node to route to in the workflow
    """
    messages: Annotated[list, add_messages]
    question_rewrite_count: int
    processing_log: List[str]
    next_workflow_node: str

def _create_retriever_tools() -> List:
    """
    Creates retriever tools for each configured Pinecone index.
    
    Returns:
        List of retriever tools for document search
        
    Raises:
        Exception: If there's an error creating retriever tools
    """
    retriever_tools = []
    
    try:
        for tool_config in CONFIG.RETRIEVER_TOOL_CONFIGS:
            langchain_vector_store = LANGCHAIN_VECTOR_STORES.get(tool_config.pinecone_index_name)
            if not langchain_vector_store:
                log.warning(f"LangChain vector store not found for index: {tool_config.pinecone_index_name}")
                continue
                
            document_retriever = langchain_vector_store.as_retriever()
            retriever_tool = create_retriever_tool(
                retriever=document_retriever,
                name=tool_config.tool_name,
                description=tool_config.tool_description,
            )
            retriever_tools.append(retriever_tool)
            
        log.success(f"Created {len(retriever_tools)} retriever tools")
        return retriever_tools
        
    except Exception as e:
        log.error("Failed to create retriever tools", e)
        raise

def analyze_question_and_decide_action(state: AgentState, llm_with_retriever_tools: ChatOpenAI) -> Dict[str, Any]:
    """
    Analyze the user's question and decide whether to use retrieval tools or respond directly.
    
    Args:
        state: Current agent state
        llm_with_retriever_tools: LLM instance with retriever tools bound
        
    Returns:
        Updated state with new messages
    """
    try:
        log.information("LLM is analyzing the question to decide on tool use")
        conversation_messages = state["messages"]
        
        if not conversation_messages:
            log.error("No messages found in state")
            return {"messages": [AIMessage(content="Tôi cần một câu hỏi để có thể hỗ trợ bạn.")]}
        
        llm_response = llm_with_retriever_tools.invoke(conversation_messages)
        log.success("Generated query/response successfully")
        return {"messages": [llm_response]}
        
    except Exception as e:
        log.error("Error in analyze_question_and_decide_action", e)
        return {"messages": [AIMessage(content="Tôi gặp lỗi khi xử lý câu hỏi của bạn.")]}

def evaluate_document_relevance(state: AgentState) -> Dict[str, str]:
    """
    Evaluate the relevance of retrieved documents and decide the next step.
    
    Args:
        state: Current agent state
        
    Returns:
        Dictionary with the next node to route to
    """
    try:
        log.information("LLM is grading documents for relevance")
        conversation_messages = state["messages"]
        
        if len(conversation_messages) < 2:
            log.error("Insufficient messages for document grading")
            return {"next_workflow_node": "generate_final_answer"}
        
        last_message = conversation_messages[-1]
        original_question = conversation_messages[0].content
        retrieved_documents = last_message.content
        log.information(f"Document: {retrieved_documents}")
        
        grading_prompt = prompts.GRADE_PROMPT.format(
            document=retrieved_documents, 
            question=original_question
        )
        
        document_grader_llm = ChatOpenAI(
            model=CONFIG.OPENAI_LLM_MODEL, 
            temperature=0, 
            api_key=CONFIG.OPENAI_API_KEY,
        )
        
        grading_result = document_grader_llm.invoke(grading_prompt)
        
        try:
            log.information(f"Grading result: {grading_result.content}")
            result_json = json.loads(grading_result.content.replace("```json", "").replace("```", ""))
            relevance_score = result_json.get("binary_score", "no")
        except (json.JSONDecodeError, AttributeError) as e:
            log.error(f"Error parsing grading response: {e}.")
            if "yes" in grading_result.content.lower():
                relevance_score = "yes"
            else:
                relevance_score = "no"
            
        log.information(f"Grading result: {relevance_score}")
        
        if relevance_score == "yes":
            log.success("Documents are relevant")
            next_node = "generate_final_answer"
        else:
            log.warning("Documents are not relevant. Will rewrite question")
            next_node = "improve_question"
            
        return {"next_workflow_node": next_node}
        
    except Exception as e:
        log.error("Error in evaluate_document_relevance", e)
        return {"next_workflow_node": "generate_final_answer"}

def improve_question(state: AgentState) -> Dict[str, Any]:
    """
    Rewrite the user's question for better retrieval results.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with rewritten question and updated counters
    """
    try:
        log.information("LLM is rewriting the question")
        current_rewrite_count = state.get("question_rewrite_count", 0)
        
        if current_rewrite_count >= CONFIG.MAX_QUESTION_REWRITES:
            log.warning("Maximum rewrites reached. Proceeding to generate answer")
            return {"next_workflow_node": "generate_final_answer"}
        
        conversation_messages = state["messages"]
        if not conversation_messages:
            log.error("No messages found for rewriting")
            return {"next_workflow_node": "generate_final_answer"}
            
        # Get the original question from the first user message
        original_question = conversation_messages[0].content
        
        question_rewriter_llm = ChatOpenAI(
            model=CONFIG.OPENAI_LLM_MODEL, 
            temperature=0.2, 
            api_key=CONFIG.OPENAI_API_KEY,
        )

        rewrite_prompt = prompts.REWRITE_PROMPT.format(question=original_question)
        rewrite_response = question_rewriter_llm.invoke(rewrite_prompt)
        
        improved_question = rewrite_response.content.strip()
        log.information(f"Rewritten question: {improved_question}")

        # Create a clean message list with the rewritten question
        rewritten_message = HumanMessage(content=improved_question)
        
        new_rewrite_count = current_rewrite_count + 1
        current_processing_log = state.get("processing_log", [])
        current_processing_log.append(f"Question rewritten (attempt #{new_rewrite_count}): {improved_question}")
        
        return {
            "messages": [rewritten_message],
            "question_rewrite_count": new_rewrite_count,
            "processing_log": current_processing_log,
            "next_workflow_node": "analyze_question_and_decide_action"
        }
        
    except Exception as e:
        log.error("Error in improve_question", e)
        return {"next_workflow_node": "generate_final_answer"}

def generate_final_answer(state: AgentState) -> Dict[str, List[BaseMessage]]:
    """
    Generate the final answer based on retrieved context.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with the final answer
    """
    try:
        log.information("LLM is generating the final answer")
        conversation_messages = state["messages"]
        user_question = ""
        retrieved_context = ""

        # Extract question and context from messages
        for msg in reversed(conversation_messages):
            if isinstance(msg, HumanMessage) and not user_question:
                user_question = msg.content
            elif isinstance(msg, ToolMessage) and not retrieved_context:
                retrieved_context = msg.content
        
        if not user_question:
            log.error("No question found in messages")
            return {"messages": [AIMessage(content="Tôi cần một câu hỏi rõ ràng để có thể trả lời.")]}
            
        if not retrieved_context:
            log.warning("No context found to generate an answer, generating from history")
            # Fallback to a conversational response using the available messages
            generation_prompt = prompts.GENERATE_WITHOUT_CONTEXT_PROMPT.format(
                chat_history=conversation_messages,
                question=user_question
            )
        else:
            generation_prompt = prompts.GENERATE_PROMPT.format(
                question=user_question, 
                context=retrieved_context
            )

        answer_generator_llm = ChatOpenAI(
            model=CONFIG.OPENAI_LLM_MODEL, 
            temperature=0, 
            api_key=CONFIG.OPENAI_API_KEY,
        )
        
        final_response = answer_generator_llm.invoke(generation_prompt)
        
        log.success("Final answer generated successfully")
        return {"messages": [final_response]}
        
    except Exception as e:
        log.error("Error in generate_final_answer", e)
        return {"messages": [AIMessage(content="Tôi gặp lỗi khi tạo câu trả lời. Vui lòng thử lại.")]}

def create_agentic_rag_workflow():
    """
    Create and compile the agentic RAG graph workflow.
    
    Returns:
        Compiled LangGraph workflow
        
    Raises:
        Exception: If there's an error creating the graph
    """
    try:
        retriever_tools = _create_retriever_tools()
        
        if not retriever_tools:
            raise Exception("No retriever tools were created")
        
        base_llm = ChatOpenAI(
            model=CONFIG.OPENAI_LLM_MODEL, 
            temperature=0, 
            api_key=CONFIG.OPENAI_API_KEY,
        )
        llm_with_retriever_tools = base_llm.bind_tools(tools=retriever_tools)
        
        log.information("Assembling the graph workflow")
        
        rag_workflow = StateGraph(AgentState)
        
        # Add nodes to the graph
        rag_workflow.add_node("analyze_question_and_decide_action", 
                             lambda state: analyze_question_and_decide_action(state, llm_with_retriever_tools))
        rag_workflow.add_node("retrieve_documents", ToolNode(retriever_tools))
        rag_workflow.add_node("improve_question", improve_question)
        rag_workflow.add_node("generate_final_answer", generate_final_answer)
        rag_workflow.add_node("evaluate_document_relevance", evaluate_document_relevance)
        
        # Set entry point
        rag_workflow.set_entry_point("analyze_question_and_decide_action")
        
        def route_after_analysis(state: AgentState) -> str:
            """Route after query generation. Decide whether to use tools or end."""
            try:
                last_message = state["messages"][-1]
                if hasattr(last_message, 'additional_kwargs') and "tool_calls" in last_message.additional_kwargs:
                    return "retrieve_documents"
                else:
                    return "generate_final_answer"
            except Exception as e:
                log.error("Error in route_after_analysis", e)
                return "generate_final_answer"
            
        def route_after_evaluation(state: AgentState) -> str:
            """Route after document grading. Read decision from state."""
            return state.get("next_workflow_node", "generate_final_answer")

        # Set up conditional edges
        rag_workflow.add_conditional_edges(
            "analyze_question_and_decide_action",
            route_after_analysis,
            {
                "retrieve_documents": "retrieve_documents",
                "generate_final_answer": "generate_final_answer"
            }
        )
        
        # Workflow: retrieve -> grade -> route based on grading result
        rag_workflow.add_edge("retrieve_documents", "evaluate_document_relevance")
        rag_workflow.add_conditional_edges(
            "evaluate_document_relevance",
            route_after_evaluation,
            {
                "generate_final_answer": "generate_final_answer",
                "improve_question": "improve_question"
            }
        )
        
        rag_workflow.add_edge("generate_final_answer", END)
        rag_workflow.add_edge("improve_question", "analyze_question_and_decide_action")
        
        # Compile the graph
        compiled_graph = rag_workflow.compile()
        log.success("Graph compiled successfully")
        
        return compiled_graph
        
    except Exception as e:
        log.error("Failed to create agentic RAG graph", e)
        raise

# Create the main RAG workflow graph
agentic_rag_graph = create_agentic_rag_workflow()

def get_answer(user_question: str):
    """
    Get the answer from the agentic RAG graph.
    
    Args:
        user_question: The user's question.
        
    Returns:
        The final answer from the AI as a string.
    """
    print("-"*100)
    log.information(f'Question: {user_question}')
    
    for workflow_chunk in agentic_rag_graph.stream({
        "messages": [
            {
                "role": "user",
                "content": user_question,
            }
        ]
    }):
        for node_name, state_update in workflow_chunk.items():
            if node_name == "generate_final_answer":
                return state_update["messages"][-1].content
    print("-"*100)