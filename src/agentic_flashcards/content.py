from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, Sequence


OPEN_LICENSES = frozenset({"cc0", "cc by 4.0", "public domain"})


class ImageSearchUnavailable(RuntimeError):
    """Raised by a search adapter when the upstream service cannot answer."""


@dataclass(frozen=True)
class TrilingualExplanation:
    chinese: str
    english: str
    japanese: str


@dataclass(frozen=True)
class ImageAsset:
    uri: str
    alt: str
    attribution: str
    license: str
    relevance_score: float = 1.0


@dataclass(frozen=True)
class EnrichedContent:
    term: str
    explanation: TrilingualExplanation
    image: ImageAsset | None
    image_source: Literal["search", "generated", "none"]
    fallback_reason: str | None = None


class ExplanationProvider(Protocol):
    def explain(self, term: str) -> TrilingualExplanation: ...


class ImageSearchProvider(Protocol):
    def search(self, query: str, *, limit: int) -> Sequence[ImageAsset]: ...


class ImageGenerationProvider(Protocol):
    def generate(self, prompt: str) -> ImageAsset: ...


class ContentOrchestrator:
    """Coordinate semantic generation and a bounded search-to-generation image fallback."""

    def __init__(
        self,
        *,
        explainer: ExplanationProvider,
        image_search: ImageSearchProvider,
        image_generator: ImageGenerationProvider,
        minimum_relevance: float = 0.75,
    ):
        if not 0 <= minimum_relevance <= 1:
            raise ValueError("minimum_relevance must be between 0 and 1")
        self.explainer = explainer
        self.image_search = image_search
        self.image_generator = image_generator
        self.minimum_relevance = minimum_relevance

    def enrich(self, term: str, *, visually_useful: bool) -> EnrichedContent:
        term = term.strip()
        if not term:
            raise ValueError("term is required")
        explanation = self.explainer.explain(term)
        self._validate_explanation(explanation)
        if not visually_useful:
            return EnrichedContent(
                term=term,
                explanation=explanation,
                image=None,
                image_source="none",
            )

        fallback_reason = "no-eligible-search-result"
        try:
            candidates = self.image_search.search(term, limit=4)
        except ImageSearchUnavailable:
            candidates = []
            fallback_reason = "search-unavailable"

        eligible = [asset for asset in candidates if self._eligible_search_asset(asset)]
        if eligible:
            image = max(eligible, key=lambda asset: asset.relevance_score)
            self._validate_asset(image)
            return EnrichedContent(
                term=term,
                explanation=explanation,
                image=image,
                image_source="search",
            )

        image = self.image_generator.generate(
            f"Create a clear educational image for the concept {term!r}; "
            "show the concept directly and do not add text."
        )
        self._validate_asset(image)
        return EnrichedContent(
            term=term,
            explanation=explanation,
            image=image,
            image_source="generated",
            fallback_reason=fallback_reason,
        )

    def _eligible_search_asset(self, asset: ImageAsset) -> bool:
        return (
            asset.license.strip().lower() in OPEN_LICENSES
            and asset.relevance_score >= self.minimum_relevance
        )

    @staticmethod
    def _validate_explanation(value: TrilingualExplanation) -> None:
        if not all(part.strip() for part in (value.chinese, value.english, value.japanese)):
            raise ValueError("all three language explanations are required")

    @staticmethod
    def _validate_asset(value: ImageAsset) -> None:
        if not value.uri.strip() or not value.alt.strip():
            raise ValueError("image uri and alt text are required")
        if not 0 <= value.relevance_score <= 1:
            raise ValueError("image relevance_score must be between 0 and 1")
