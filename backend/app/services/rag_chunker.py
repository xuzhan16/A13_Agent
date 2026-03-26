class RagChunker:
    def __init__(self, chunk_size: int = 480, overlap: int = 80) -> None:
        self.chunk_size = max(120, chunk_size)
        self.overlap = max(0, min(overlap, self.chunk_size // 2))

    def chunk(self, text: str) -> list[tuple[str, int, int]]:
        content = str(text or '').replace('\r\n', '\n').strip()
        if not content:
            return []

        spans: list[tuple[str, int, int]] = []
        start = 0
        length = len(content)
        while start < length:
            provisional_end = min(start + self.chunk_size, length)
            end = self._find_breakpoint(content, start, provisional_end)
            segment = content[start:end].strip()
            if segment:
                spans.append((segment, start, end))
            if end >= length:
                break
            next_start = max(end - self.overlap, start + 1)
            while next_start < length and content[next_start].isspace():
                next_start += 1
            start = next_start
        return spans

    @staticmethod
    def _find_breakpoint(content: str, start: int, provisional_end: int) -> int:
        if provisional_end >= len(content):
            return len(content)
        search_start = max(start, provisional_end - 80)
        search_window = content[search_start:provisional_end]
        for marker in ['\n\n', '\n', '?', '.', ';', '?', '!', '?']:
            position = search_window.rfind(marker)
            if position >= 0:
                return max(search_start + position + len(marker), start + 1)
        return provisional_end
