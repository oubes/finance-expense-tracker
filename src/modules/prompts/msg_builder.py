# ---- Msg Builder Class ----
class MsgBuilder:
    # ---- Constructor ----
    def __init__(self, default_system_prompt: str = "You are a helpful assistant."):
        self.default_system_prompt = default_system_prompt

    # ---- Message Construction ----
    def build(
        self,
        system_prompt: str,
        user_prompt: str,
        question: str,
        context: str,
        retrieval_chunks: list[str],
    ) -> list[dict]:

        system_content = system_prompt or self.default_system_prompt

        question = question or ""
        context = context or ""
        retrieval_chunks = retrieval_chunks or []
        
        try:
            user_content = user_prompt.format(
                context=context,
                question=question
            )
        except Exception:
            user_content = user_prompt

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]