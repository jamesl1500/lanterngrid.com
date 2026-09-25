import pytest

from app.modules.posts.text import hashtags, mentions, strip_code


def test_strip_code_removes_fences_and_inline_code() -> None:
    md = "before `#nope @nope`\n```python\n# comment @decorator\n```\nafter #yes"
    stripped = strip_code(md)
    assert "#nope" not in stripped and "@decorator" not in stripped
    assert "#yes" in stripped


def test_an_unclosed_fence_hides_the_rest() -> None:
    assert hashtags("#before\n```\n#inside") == ["before"]


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("Shipping #Rust and #postgres today", ["Rust", "postgres"]),
        ("I like #rust. And #Rust again", ["rust"]),
        ("#C++ and #C# and #node.js", ["C++", "C#", "node.js"]),
        ("issue #42, a#b, &#39; and https://x.dev/#anchor", []),
        ("(#go)", ["go"]),
    ],
)
def test_hashtags(markdown: str, expected: list[str]) -> None:
    assert hashtags(markdown) == expected


def test_hashtags_are_capped() -> None:
    assert len(hashtags(" ".join(f"#tag{i}" for i in range(20)))) == 10


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("thanks @Ada and @ben_o!", ["ada", "ben_o"]),
        ("mail ada@example.com or see x.com/@ada", []),
        ("@ada @ADA", ["ada"]),
        ("`@ada` in code", []),
    ],
)
def test_mentions(markdown: str, expected: list[str]) -> None:
    assert mentions(markdown) == expected
