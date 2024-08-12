from collections import defaultdict

import ixmp
import pytest

from message_ix.models import MESSAGE, MESSAGE_MACRO, shift_period
from message_ix.testing import make_dantzig


def test_initialize(test_mp):
    # Expected numbers of items by type
    exp = defaultdict(list)
    for name, spec in MESSAGE.items.items():
        exp[str(spec.type.name).lower()].append(name)

    # Use ixmp.Scenario to avoid invoking ixmp_source/Java code that
    # automatically populates empty scenarios
    s = ixmp.Scenario(test_mp, "test_initialize", "test_initialize", version="new")

    # Initialization succeeds on a totally empty scenario
    MESSAGE.initialize(s)

    # The expected items exist
    for ix_type, exp_names in exp.items():
        obs_names = getattr(s, f"{ix_type}_list")()
        assert sorted(obs_names) == sorted(exp_names)


def test_message_macro():
    # Constructor runs successfully
    MESSAGE_MACRO()

    class _MM(MESSAGE_MACRO):
        """Dummy subclass requiring a non-existent GAMS version."""

        GAMS_min_version = "99.9.9"

    # Constructor complains about an insufficient GAMS version
    with pytest.raises(
        RuntimeError, match="MESSAGE-MACRO requires GAMS >= " "99.9.9; found "
    ):
        _MM()

    # Construct with custom model options
    mm = MESSAGE_MACRO(
        convergence_criterion=0.02, max_adjustment=0.4, max_iteration=100
    )

    # Command-line options to GAMS have expected form
    expected = [
        "--CONVERGENCE_CRITERION=0.02",
        "--MAX_ADJUSTMENT=0.4",
        "--MAX_ITERATION=100",
    ]
    assert all(e in mm.solve_args for e in expected)


@pytest.mark.parametrize(
    "y0",
    (
        # Not implemented: shifting to an earlier period
        pytest.param(1962, marks=pytest.mark.xfail(raises=NotImplementedError)),
        # Does nothing
        1963,
        # Not implemented with ixmp.JDBCBackend
        pytest.param(1964, marks=pytest.mark.xfail(raises=NotImplementedError)),
        pytest.param(1965, marks=pytest.mark.xfail(raises=NotImplementedError)),
    ),
)
def test_shift_period(test_mp, y0):
    s = make_dantzig(test_mp, solve=True, multi_year=True)

    shift_period(s, y0)
