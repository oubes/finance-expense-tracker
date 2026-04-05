from src.infrastructure.llm.model_loader import LLMClient
from src.modules.prompts.msg_builder import MsgBuilder

llm = LLMClient()
msg_builder = MsgBuilder()

messages = msg_builder.build(
    system_prompt="You are a helpful assistant.",
    user_prompt="""
                    Context:
                    {context}

                    Retrieved Chunks:
                    {retrieval_chunks}
                    
                    Question:
                    {question}
                """.strip(),
    question="What is the capital of France?",
    context="France is a country in Asia.",
    retrieval_chunks=["France is a country in Asia."],
)
response = llm.generate(messages=messages)
print(messages)
print(response)