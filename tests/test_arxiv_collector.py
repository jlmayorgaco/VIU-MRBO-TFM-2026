"""Tests for the arXiv literature collector."""

from viu_mrob_tfm.literature.arxiv import (
    build_api_url,
    build_submitted_date_query,
    filename_for_paper,
    parse_atom_feed,
    publication_year,
    slugify,
)


ATOM_FIXTURE = """\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.01234v2</id>
    <updated>2024-02-01T00:00:00Z</updated>
    <published>2024-01-01T00:00:00Z</published>
    <title> Distributed Multi-Robot Transport over Graphs </title>
    <summary>
      A compact abstract about cooperative payload transport.
    </summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Grace Hopper</name></author>
    <arxiv:primary_category term="cs.RO" />
    <category term="cs.RO" />
    <category term="eess.SY" />
    <link href="http://arxiv.org/abs/2401.01234v2" rel="alternate" type="text/html" />
    <link title="pdf" href="http://arxiv.org/pdf/2401.01234v2" rel="related" type="application/pdf" />
  </entry>
</feed>
"""


def test_build_api_url_encodes_query() -> None:
    url = build_api_url('all:"multi robot" AND cat:cs.RO', start=10, max_results=25)

    assert "export.arxiv.org/api/query" in url
    assert "start=10" in url
    assert "max_results=25" in url
    assert "search_query=all%3A%22multi+robot%22" in url


def test_parse_atom_feed_normalizes_paper_metadata() -> None:
    papers = parse_atom_feed(ATOM_FIXTURE)

    assert len(papers) == 1
    paper = papers[0]
    assert paper.arxiv_id == "2401.01234"
    assert paper.version == "v2"
    assert paper.title == "Distributed Multi-Robot Transport over Graphs"
    assert paper.authors == ("Ada Lovelace", "Grace Hopper")
    assert paper.primary_category == "cs.RO"
    assert paper.categories == ("cs.RO", "eess.SY")
    assert paper.pdf_url == "http://arxiv.org/pdf/2401.01234v2"


def test_filename_for_paper_is_deterministic_and_safe() -> None:
    paper = parse_atom_feed(ATOM_FIXTURE)[0]

    assert filename_for_paper(paper) == (
        "2401.01234v2__distributed-multi-robot-transport-over-graphs.pdf"
    )


def test_slugify_falls_back_for_empty_titles() -> None:
    assert slugify("  !!!  ") == "untitled"


def test_build_submitted_date_query_wraps_original_query() -> None:
    query = build_submitted_date_query('all:"multi robot" AND cat:cs.RO', 2024)

    assert query == (
        '(all:"multi robot" AND cat:cs.RO) '
        "AND submittedDate:[202401010000 TO 202412312359]"
    )


def test_publication_year_uses_published_date() -> None:
    paper = parse_atom_feed(ATOM_FIXTURE)[0]

    assert publication_year(paper) == "2024"
