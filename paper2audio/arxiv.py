import sys
from typing import NamedTuple

import requests
from lxml import html, etree


def extract_texts_impl(node: etree._Element, tags: set[str], dest: list[str]) -> None:
    for i in range(len(node)):
        child = node[i]
        if child.tag in tags:
            dest.append(child.text_content().strip())
            continue
        extract_texts_impl(child, tags, dest)


def extract_texts(node: etree._Element, tags: set[str]) -> list[str]:
    texts = []
    extract_texts_impl(node, tags, texts)
    return texts


class PaperTexts(NamedTuple):
    abstract: str
    sections: list[list[str]]


def parse_html(html: etree._ElementTree) -> PaperTexts:
    math_nodes = html.xpath("//math")
    for node in math_nodes:
        node.getparent().replace(node, etree.fromstring(f'<span>&lt;an expression&gt;</span>'))

    abstract_node = html.xpath("//div[@class = 'ltx_abstract']")
    if len(abstract_node) == 1:
        abstract = extract_texts(abstract_node[0], {"p"})
    else:
        abstract = ""

    section_nodes = html.xpath("//section")
    texts = []
    for node in section_nodes:
        if list(node.classes) != ["ltx_section"]:
            continue

        texts.append(extract_texts(node, {"p", "h1", "h2", "h3", "h4", "h5", "h6"}))

    return PaperTexts(abstract=abstract, sections=texts)


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
