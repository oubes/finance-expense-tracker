from langchain_text_splitters import RecursiveCharacterTextSplitter

class DynamicSplitter:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def get_splitter(self, text: str) -> RecursiveCharacterTextSplitter:
        target_size = self.chunk_size

        return RecursiveCharacterTextSplitter(
            chunk_size=target_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=["\n\n", "\n", " ", ""]
        )