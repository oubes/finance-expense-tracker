from src.pipelines.v1.aug_gen_pipeline import AugGenPipeline

class RAGWorkflow:
    def __init__(self, aug_gen_pipeline: AugGenPipeline):
        self.aug_gen_pipeline = aug_gen_pipeline   

    async def run(self):
        return await self.aug_gen_pipeline.run(
            queries=[
                {
                    "user_question": (
                        "i'm getting paid 7200 EGP per month, and i want to save 2200 EGP, how should i divide my expenses? i need a list"
                        "like how much for food, how much for transportation, how much for entertainment, etc."
                    ),
                    "chunks": (
                        "Budgeting involves categorizing expenses into fixed and variable costs. "
                        "A common strategy is to prioritize essential expenses, reduce discretionary spending, "
                        "and allocate a portion of income toward savings. Tracking expenses regularly helps identify inefficiencies. "
                        "Setting financial goals and maintaining discipline improves long-term financial stability."
                    )
                }
            ]
        )