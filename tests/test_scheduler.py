from agentic_flashcards.scheduler import next_schedule


def test_scheduler_is_deterministic_and_rating_bounded():
    result = next_schedule(
        reviewed_on="2030-01-01", rating=3, interval_days=10, ease=200, repetitions=3
    )
    assert result.due_on == "2030-01-23"
    assert result.interval_days == 22
    assert result.ease == 210
