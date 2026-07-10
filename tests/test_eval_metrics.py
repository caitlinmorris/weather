from presence.eval.run_eval import cohen_kappa, entropy


def test_kappa_perfect_agreement():
    pairs = [("building", "building")] * 10 + [("debugging", "debugging")] * 10
    assert cohen_kappa(pairs) == 1.0


def test_kappa_chance_level_is_zero_ish():
    # Alternating disagreement with balanced marginals -> kappa near 0.
    pairs = [("a", "a"), ("a", "b"), ("b", "a"), ("b", "b")] * 5
    k = cohen_kappa(pairs)
    assert k is not None and abs(k) < 0.01


def test_kappa_degenerate_returns_none():
    assert cohen_kappa([("a", "a")] * 5) is None  # pe == 1


def test_entropy_bounds():
    assert entropy(["x"] * 10) == 0.0                    # constant field
    assert abs(entropy(["a", "b", "a", "b"]) - 1.0) < 1e-9  # fair coin
    assert entropy([]) == 0.0
