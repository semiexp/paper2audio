import sys
from typing import NamedTuple

import requests
from lxml import html, etree


def extract_texts_impl(node: etree._Element, tags: set[str], dest: list[tuple[str, str]]) -> None:
    for i in range(len(node)):
        child = node[i]
        if child.tag in tags:
            dest.append((child.tag, child.text_content().strip().replace("  ", " ")))
            continue
        extract_texts_impl(child, tags, dest)


def extract_texts(node: etree._Element, tags: set[str]) -> tuple[list[str], list[str]]:
    tag_and_texts = []
    extract_texts_impl(node, tags, tag_and_texts)

    ext_tags = [t for t, _ in tag_and_texts]
    texts = [text for _, text in tag_and_texts]

    return ext_tags, texts


class PaperTexts(NamedTuple):
    abstract: str
    tags: list[list[str]]
    sections: list[list[str]]
    math_exprs: list[str]

    def all_tags(self) -> list[str]:
        ret = ["p"]  # for abstract
        for tag in self.tags:
            ret.extend(tag)
        return ret

    def texts(self) -> list[str]:
        ret = [self.abstract]
        for section in self.sections:
            ret.extend(section)
        return ret

    def restore_math_expr(self, text: str) -> list[str]:
        while "[a math expression" in text:
            start = text.find("[a math expression")
            end = text.find("]", start)
            idx = int(text[start + 18:end])
            text = text[:start] + f"${self.math_exprs[idx]}$" + text[end + 1:]
        return text


def parse_html(html: etree._ElementTree) -> PaperTexts:
    math_nodes = html.xpath("//math")
    original_math_exprs = []
    for i, node in enumerate(math_nodes):
        original_math_exprs.append(node.attrib["alttext"])
        node.getparent().replace(node, etree.fromstring(f'<span> [a math expression {i}] {node.tail or ""} </span>'))

    abstract_node = html.xpath("//div[@class = 'ltx_abstract']")
    if len(abstract_node) == 1:
        abstract = "\n\n".join(extract_texts(abstract_node[0], {"p"})[1])
    else:
        abstract = ""

    section_nodes = html.xpath("//section")
    tags = []
    texts = []
    for node in section_nodes:
        if list(node.classes) != ["ltx_section"]:
            continue

        tg, tt = extract_texts(node, {"p", "h1", "h2", "h3", "h4", "h5", "h6"})
        tags.append(tg)
        texts.append(tt)

    return PaperTexts(abstract=abstract, tags=tags, sections=texts, math_exprs=original_math_exprs)


def load_from_arxiv(url: str) -> PaperTexts:
    resp = requests.get(url)
    text = resp.text

    root = html.fromstring(text)
    return parse_html(root)


def main() -> None:
    texts = load_from_arxiv(sys.argv[1])
    print(texts.abstract)
    for section in texts.sections:
        print("=" * 80)
        print("\n\n".join(section))


if __name__ == "__main__":
    main()
