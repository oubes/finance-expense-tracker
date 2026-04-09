class RAGWorkflow:
    def __init__(self, aug_gen_pipeline, hybrid_retriever):
        self.hybrid_retriever = hybrid_retriever
        self.aug_gen_pipeline = aug_gen_pipeline

    async def run(self):
        # ---- Retrieval ----
        result = await self.hybrid_retriever.search(
            input_query="how many users my system must be able of handling?"
        )

        print("Retrieval Result:")
        print(result)

        # ---- Augmentation + Generation ----
        return await self.aug_gen_pipeline.run(
            queries=[
                {
                    "user_question": (
                        "i'm getting paid 7200 EGP per month, and i want to save 2200 EGP, "
                        "how should i divide my expenses?"
                    ),
                    "chunks": " ".join([d["text"] for d in result]),
                }
            ]
        )