from langchain_text_splitters import RecursiveCharacterTextSplitter


class DynamicSplitter:
    def __init__(self, base_chunk_size: int, chunk_overlap: int):
        self.base_chunk_size = base_chunk_size
        self.chunk_overlap = chunk_overlap

    def get_splitter(self, text: str) -> RecursiveCharacterTextSplitter:
        length = len(text)

        if length < 1000:
            chunk_size = 300
        elif length < 3000:
            chunk_size = self.base_chunk_size
        else:
            chunk_size = 800

        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ".", "•", "-", " "],
        )