from agentic_flashcards import CardConflict, FlashcardStore


def test_offline_upsert_conflict_and_idempotent_replay(tmp_path):
    store = FlashcardStore(tmp_path / "cards.sqlite")
    created = store.upsert(
        operation_id="create-1",
        card_id="card-1",
        front="Question",
        back="Answer",
        tags=["demo"],
        expected_version=0,
    )
    replay = store.upsert(
        operation_id="create-1",
        card_id="card-1",
        front="Question",
        back="Answer",
        tags=["demo"],
        expected_version=0,
    )
    assert replay == created

    store.upsert(
        operation_id="edit-1",
        card_id="card-1",
        front="Better question",
        back="Answer",
        tags=["demo"],
        expected_version=1,
    )
    try:
        store.upsert(
            operation_id="offline-edit",
            card_id="card-1",
            front="Stale question",
            back="Answer",
            expected_version=1,
        )
    except CardConflict as error:
        assert error.current["version"] == 2
        assert error.current["front"] == "Better question"
    else:
        raise AssertionError("stale mutation must conflict")


def test_review_is_append_only_and_retry_safe(tmp_path):
    store = FlashcardStore(tmp_path / "cards.sqlite")
    store.upsert(
        operation_id="create",
        card_id="card-1",
        front="Question",
        back="Answer",
        expected_version=0,
    )
    first = store.review(
        operation_id="review-1", card_id="card-1", reviewed_on="2030-01-01", rating=2
    )
    replay = store.review(
        operation_id="review-1", card_id="card-1", reviewed_on="2030-01-01", rating=2
    )
    assert first == replay
    assert first["due_on"] == "2030-01-02"
    count = store.conn.execute("SELECT COUNT(*) FROM review_events").fetchone()[0]
    assert count == 1


def test_change_cursor_supports_incremental_sync(tmp_path):
    store = FlashcardStore(tmp_path / "cards.sqlite")
    store.upsert(
        operation_id="create-1", card_id="one", front="One", back="1", expected_version=0
    )
    first = store.changes()
    store.upsert(
        operation_id="create-2", card_id="two", front="Two", back="2", expected_version=0
    )
    second = store.changes(first["cursor"])
    assert [card["id"] for card in second["cards"]] == ["two"]
