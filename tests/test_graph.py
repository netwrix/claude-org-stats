from src.graph import make_graph


class TestMakeGraph:
    def test_zero_percent(self):
        result = make_graph(0, bar_length=10)
        assert result == "░" * 10
        assert len(result) == 10

    def test_hundred_percent(self):
        result = make_graph(100, bar_length=10)
        assert result == "█" * 10
        assert len(result) == 10

    def test_fifty_percent(self):
        result = make_graph(50, bar_length=10)
        assert result == "█████░░░░░"
        assert len(result) == 10

    def test_default_bar_length(self):
        result = make_graph(50)
        assert len(result) == 25

    def test_custom_blocks(self):
        result = make_graph(50, bar_length=10, blocks="⬜⬛")
        assert result == "⬛⬛⬛⬛⬛⬜⬜⬜⬜⬜"

    def test_rounding(self):
        result = make_graph(33.33, bar_length=10)
        # 33.33% of 10 = 3.333, rounds to 3
        assert result.count("█") == 3
        assert len(result) == 10

    def test_very_small_percent(self):
        result = make_graph(1, bar_length=10)
        # 1% of 10 = 0.1, rounds to 0
        assert len(result) == 10

    def test_bar_length_one(self):
        result = make_graph(100, bar_length=1)
        assert result == "█"

    def test_multi_block_mode(self):
        # With 4 blocks: ░▒▓█ (3 fill levels)
        result = make_graph(100, bar_length=5, blocks="░▒▓█")
        assert result == "█████"

    def test_multi_block_zero(self):
        result = make_graph(0, bar_length=5, blocks="░▒▓█")
        assert result == "░░░░░"

    def test_multi_block_partial(self):
        # With "░▒▓█", 3 fill levels, bar_length=5, total_units=15
        # 50% of 15 = 7.5, rounds to 8 -> 2 full + remainder 2 -> "██▓░░"
        result = make_graph(50, bar_length=5, blocks="░▒▓█")
        assert len(result) == 5
        assert "█" in result

    def test_fallback_short_blocks(self):
        # Single char blocks should fall back to default
        result = make_graph(50, bar_length=10, blocks="x")
        assert len(result) == 10

    def test_negative_clamps_to_zero(self):
        result = make_graph(-10, bar_length=10)
        assert result == "░" * 10

    def test_over_100_clamps(self):
        result = make_graph(150, bar_length=10)
        assert result == "█" * 10
