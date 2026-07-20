import pytest

from agentic_flashcards.content import (
    ContentOrchestrator,
    ImageAsset,
    ImageSearchUnavailable,
    TrilingualExplanation,
)


class Explainer:
    def explain(self, term: str) -> TrilingualExplanation:
        return TrilingualExplanation("中文解释", "English explanation", "日本語の説明")


class Search:
    def __init__(self, results=(), *, unavailable: bool = False):
        self.results = results
        self.unavailable = unavailable
        self.calls = 0

    def search(self, query: str, *, limit: int):
        self.calls += 1
        if self.unavailable:
            raise ImageSearchUnavailable("synthetic outage")
        return self.results[:limit]


class Generator:
    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> ImageAsset:
        self.calls += 1
        return ImageAsset("generated://image", "Generated image", "demo", "model-generated")


def orchestrator(search: Search, generator: Generator) -> ContentOrchestrator:
    return ContentOrchestrator(
        explainer=Explainer(), image_search=search, image_generator=generator
    )


def test_prefers_relevant_open_license_search_result():
    weak = ImageAsset("https://example.invalid/weak", "Weak", "source", "CC0", 0.5)
    strong = ImageAsset(
        "https://example.invalid/strong", "Strong", "source", "CC BY 4.0", 0.9
    )
    generator = Generator()
    result = orchestrator(Search([weak, strong]), generator).enrich(
        "orbit", visually_useful=True
    )

    assert result.image == strong
    assert result.image_source == "search"
    assert generator.calls == 0


@pytest.mark.parametrize("unavailable", [False, True])
def test_falls_back_to_generation_when_search_cannot_supply_an_image(unavailable):
    generator = Generator()
    result = orchestrator(Search(unavailable=unavailable), generator).enrich(
        "orbit", visually_useful=True
    )

    assert result.image_source == "generated"
    assert result.fallback_reason == (
        "search-unavailable" if unavailable else "no-eligible-search-result"
    )
    assert generator.calls == 1


def test_nonvisual_content_skips_both_image_providers():
    search = Search()
    generator = Generator()
    result = orchestrator(search, generator).enrich("because", visually_useful=False)

    assert result.image is None
    assert result.image_source == "none"
    assert search.calls == 0
    assert generator.calls == 0


def test_requires_all_three_explanations():
    class IncompleteExplainer:
        def explain(self, term: str) -> TrilingualExplanation:
            return TrilingualExplanation("中文解释", "English explanation", "")

    with pytest.raises(ValueError, match="all three"):
        ContentOrchestrator(
            explainer=IncompleteExplainer(),
            image_search=Search(),
            image_generator=Generator(),
        ).enrich("orbit", visually_useful=False)
