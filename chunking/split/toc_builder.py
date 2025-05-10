from chunking.base import BaseOperation, Chunk, ChunkGroup, CType


class TOCBuilder(BaseOperation):

    @classmethod
    def run(
        cls,
        chunks: Chunk | ChunkGroup,
        **kwargs,
    ) -> ChunkGroup:
        """Group chunk by preceding header,
        assuming the reading order is correct"""

        if isinstance(chunks, Chunk):
            chunks = ChunkGroup([chunks])

        output = ChunkGroup()
        for root in chunks:
            cur_root_children = []
            cur_header_chunk = None
            cur_header_children = []

            for _, child_chunk in root.walk():
                new_child_chunk = child_chunk.clone_without_relations()

                if new_child_chunk.ctype == CType.Root:
                    continue
                if new_child_chunk.ctype == CType.Header:
                    if cur_header_chunk and cur_header_children:
                        cur_header_chunk.add_children(cur_header_children)

                    cur_header_chunk = new_child_chunk
                    cur_root_children.append(cur_header_chunk)
                    cur_header_children = []
                else:
                    if cur_header_chunk:
                        cur_header_children.append(new_child_chunk)
                    else:
                        cur_root_children.append(new_child_chunk)

            if cur_header_chunk and cur_header_children:
                cur_header_chunk.add_children(cur_header_children)

            # remove children from root
            new_root = root.clone_without_relations()
            new_root.add_children(cur_root_children)
            output.append(new_root)

        return output
