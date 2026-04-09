from src.pipelines.v1.aug_gen_pipeline import AugGenPipeline
from src.bootstrap.dependencies.rag import get_aug_gen_pipeline



class RAGWorkflow:
    def __init__(self, aug_gen_pipeline: AugGenPipeline):
        self.aug_gen_pipeline = aug_gen_pipeline   
    def run(self):
        return self.aug_gen_pipeline.run()