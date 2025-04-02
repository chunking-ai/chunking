from chunking.base import BaseOperation, Chunk, ChunkGroup


def map_bytestring_index_to_string_index(byte_string, byte_indices):
    """Convert the bytestring index to string index"""
    # Sort indices to process them in order
    sorted_indices = sorted(byte_indices)

    # Create a mapping from byte indices to character indices
    byte_to_char_map = {}

    # Initialize counters
    char_count = 0

    # Process each byte and track character positions
    start = 0
    for byte_pos in sorted_indices:
        char = byte_string[start:byte_pos].decode("utf-8")
        char_count += len(char)
        byte_to_char_map[byte_pos] = char_count
        start = byte_pos

    # Return the results in the original order
    return byte_to_char_map


def parse_tree_sitter_node(node):
    ...


class Markdown(BaseOperation):
    @classmethod
    def run(
        cls,
        chunk: Chunk | ChunkGroup,
        **kwargs,
    ) -> ChunkGroup:
        """Split large chunks of text into smaller chunks based on Markdown heading,
        where each chunk is not larger than a given size.

        Args:
            min_chunk_size: the minimum size of a chunk. If a chunk is smaller than
                this size, it will be merged with the next chunk. If -1, there is
                no minimum.
        """
        import tree_sitter_markdown
        from tree_sitter import Language, Parser

        # Resolve chunk
        if isinstance(chunk, Chunk):
            chunk = ChunkGroup(chunks=[chunk])

        # Resolve length function
        parser = Parser(Language(tree_sitter_markdown.language()))

        output = ChunkGroup()
        for mc in chunk:
            ct = mc.content
            ctb = ct.encode("utf-8")
            if not isinstance(ct, str):
                output.add_group(ChunkGroup(root=mc))
                continue

            tree = parser.parse(ctb)
            ts_root = tree.root_node

            # Get chunk header range
            stack, h_start, h_end, level = [ts_root], [], {}, []
            while stack:
                ts_node = stack.pop()
                if "heading" in ts_node.type:
                    lvl = None
                    for child in ts_node.children:
                        if child.type == "atx_h1_marker":
                            lvl = 1
                        elif child.type == "atx_h2_marker":
                            lvl = 2
                        elif child.type == "atx_h3_marker":
                            lvl = 3
                        elif child.type == "atx_h4_marker":
                            lvl = 4
                        elif child.type == "atx_h5_marker":
                            lvl = 5
                        elif child.type == "atx_h6_marker":
                            lvl = 6
                        elif child.type == "setext_h1_underline":
                            lvl = 1
                        elif child.type == "setext_h2_underline":
                            lvl = 2

                    if lvl is None:
                        continue

                    h_start.append(ts_node.start_byte)
                    h_end[ts_node.start_byte] = ts_node.end_byte
                    level.append(lvl)

                for i in range(ts_node.child_count - 1, -1, -1):
                    if child := ts_node.children[i]:
                        stack.append(child)

            if len(h_start) < 2:
                # 1 or 0 heading, so nothing to split
                output.add_group(ChunkGroup(root=mc))
                continue

            # Convert from byte index to character index
            byte_to_char_map = map_bytestring_index_to_string_index(
                ctb, h_start + list(h_end.values())
            )
            h_start = [byte_to_char_map[idx] for idx in h_start]
            h_end = {
                byte_to_char_map[idx]: byte_to_char_map[end]
                for idx, end in h_end.items()
            }

            # Build the chunks
            result = []
            parents = []
            prev, prev_lvl = mc, 0
            for idx in range(len(h_start)):
                lvl = level[idx]
                start_idx = h_start[idx]
                end_idx = h_end[start_idx]
                heading = ct[start_idx:end_idx].strip()

                if idx == 0:
                    # Also include the content before the first heading
                    start_idx = 0

                if lvl > prev_lvl:
                    parents.append((prev, prev_lvl))
                    prev, prev_lvl = None, lvl
                elif lvl < prev_lvl:
                    prev, prev_lvl = parents.pop()

                if idx + 1 == len(h_start):
                    content = ct[start_idx:]
                    text = content
                else:
                    content = ct[start_idx : h_start[idx + 1]]
                    for i_ in range(idx, len(h_start)):
                        if level[i_] <= lvl:
                            text = ct[start_idx : h_start[i_]]
                    else:
                        text = content

                chunk = Chunk(
                    mimetype="plain/text",
                    content=content,
                    text=text,
                    origin=mc.origin,
                    parent=parents[-1][0],
                    prev=prev,
                    metadata={
                        "heading_level": lvl,
                        "heading": heading,
                    },
                    history=mc.history
                    + [cls.name(min_chunk_size=min_chunk_size, length_fn=length_fn)],
                )
                result.append(chunk)
                if prev is not None:
                    prev.next = chunk
                else:
                    parents[-1][0].child = chunk
                prev = chunk

            output.add_group(ChunkGroup(root=mc, chunks=result))

        return output

    @classmethod
    def py_dependency(cls) -> list[str]:
        return ["tree-sitter", "tree-sitter-markdown"]

