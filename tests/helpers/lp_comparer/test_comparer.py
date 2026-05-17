"""Unit tests for the semantic LP model comparer."""

import textwrap
from pathlib import Path

from tests.helpers.lp_comparer.comparer import compare_lp


# ---------------------------------------------------------------------------
# LP file fixtures helpers
# ---------------------------------------------------------------------------

def _write_lp(tmp_path: Path, filename: str, content: str) -> Path:
    """Write *content* to *filename* inside *tmp_path* and return the path."""
    path = tmp_path / filename
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


_BASE_LP = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """


# ---------------------------------------------------------------------------
# Identical models
# ---------------------------------------------------------------------------

class TestIdenticalModels:
    def test__compare_lp__identical_files__returns_empty_list(self, tmp_path):
        # ARRANGE
        lp1 = _write_lp(tmp_path, "a.lp", _BASE_LP)
        lp2 = _write_lp(tmp_path, "b.lp", _BASE_LP)

        # ACT
        diffs = compare_lp(lp1, lp2)

        # ASSERT
        assert diffs == []


# ---------------------------------------------------------------------------
# Model-level differences
# ---------------------------------------------------------------------------

_MINIMAL_LP_TEMPLATE = """\
    \\* {name} *\\

    max
    obj:
    +1 x

    s.t.

    bounds
       0 <= x <= 1
    binary
      x
    end
    """


class TestModelMetadata:
    def test__compare_lp__name_differs__reports_model_modified(self, tmp_path):
        # ARRANGE
        lp1 = _write_lp(tmp_path, "a.lp", _MINIMAL_LP_TEMPLATE.format(name="model_a"))
        lp2 = _write_lp(tmp_path, "b.lp", _MINIMAL_LP_TEMPLATE.format(name="model_b"))

        # ACT
        diffs = compare_lp(lp1, lp2)

        # ASSERT
        model_diffs = [d for d in diffs if d.category == "model" and d.diff_type == "modified"]
        assert any("name" in d.detail.lower() for d in model_diffs)

    def test__compare_lp__sense_differs__reports_model_modified(self, tmp_path):
        # ARRANGE
        lp1 = _write_lp(tmp_path, "a.lp", """\
            \\* m *\\

            max
            obj:
            +1 x

            s.t.

            bounds
               0 <= x <= 1
            binary
              x
            end
            """)
        lp2 = _write_lp(tmp_path, "b.lp", """\
            \\* m *\\

            min
            obj:
            +1 x

            s.t.

            bounds
               0 <= x <= 1
            binary
              x
            end
            """)

        # ACT
        diffs = compare_lp(lp1, lp2)

        # ASSERT
        sense_diffs = [d for d in diffs if d.category == "model" and "sense" in d.detail.lower()]
        assert len(sense_diffs) == 1
        assert sense_diffs[0].expected == "maximize"
        assert sense_diffs[0].actual == "minimize"


# ---------------------------------------------------------------------------
# Variable differences
# ---------------------------------------------------------------------------

class TestVariableDifferences:
    def test__compare_lp__variable_missing_in_actual__reports_missing(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual_content = """\
            \\* model *\\

            max
            obj:
            +10 x

            s.t.

            c1:
            +1 x
            <= 100

            bounds
               0 <= x <= 1
            binary
              x
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", actual_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        missing = [d for d in diffs if d.category == "variable" and d.diff_type == "missing"]
        assert any(d.name == "y" for d in missing)

    def test__compare_lp__extra_variable_in_actual__reports_extra(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        extra_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y
            +5 z

            s.t.

            c1:
            +1 x
            +2 y
            +1 z
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
               0 <= z <= 1
            binary
              x
              y
              z
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", extra_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        extra = [d for d in diffs if d.category == "variable" and d.diff_type == "extra"]
        assert any(d.name == "z" for d in extra)

    def test__compare_lp__variable_type_changed__reports_modified(self, tmp_path):
        # ARRANGE
        expected_content = """\
            \\* model *\\

            max
            obj:
            +1 x

            s.t.

            bounds
               0 <= x <= 1
            binary
              x
            end
            """
        actual_content = """\
            \\* model *\\

            max
            obj:
            +1 x

            s.t.

            bounds
               0 <= x <= 10
            general
              x
            end
            """
        expected = _write_lp(tmp_path, "expected.lp", expected_content)
        actual = _write_lp(tmp_path, "actual.lp", actual_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        type_diffs = [d for d in diffs if d.category == "variable" and d.diff_type == "modified"]
        assert any(d.name == "x" for d in type_diffs)


# ---------------------------------------------------------------------------
# Objective differences
# ---------------------------------------------------------------------------

class TestObjectiveDifferences:
    def test__compare_lp__objective_coefficient_differs__reports_modified(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        modified_content = """\
            \\* model *\\

            max
            obj:
            +99 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", modified_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        obj_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
        assert len(obj_diffs) == 1
        assert obj_diffs[0].expected == 10.0
        assert obj_diffs[0].actual == 99.0

    def test__compare_lp__variable_missing_from_objective__reports_missing(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        missing_term_content = """\
            \\* model *\\

            max
            obj:
            +10 x

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", missing_term_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        obj_missing = [d for d in diffs if d.category == "objective" and d.diff_type == "missing"]
        assert any("y" in d.detail for d in obj_missing)


# ---------------------------------------------------------------------------
# Constraint differences
# ---------------------------------------------------------------------------

class TestConstraintDifferences:
    def test__compare_lp__constraint_missing_in_actual__reports_missing(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        no_constraint_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", no_constraint_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        missing = [d for d in diffs if d.category == "constraint" and d.diff_type == "missing"]
        assert any(d.name == "c1" for d in missing)

    def test__compare_lp__extra_constraint_in_actual__reports_extra(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        extra_con_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            c2:
            +1 x
            <= 5

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", extra_con_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        extra = [d for d in diffs if d.category == "constraint" and d.diff_type == "extra"]
        assert any(d.name == "c2" for d in extra)

    def test__compare_lp__constraint_sense_changed__reports_modified(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        gte_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            >= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", gte_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        sense_diffs = [
            d for d in diffs
            if d.category == "constraint" and d.diff_type == "modified" and d.name == "c1"
            and "sense" in d.detail.lower()
        ]
        assert len(sense_diffs) == 1
        assert sense_diffs[0].expected == "LTE"
        assert sense_diffs[0].actual == "GTE"

    def test__compare_lp__constraint_rhs_changed__reports_modified(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        rhs_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 999

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", rhs_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        rhs_diffs = [
            d for d in diffs
            if d.category == "constraint" and d.diff_type == "modified" and "rhs" in d.detail.lower()
        ]
        assert len(rhs_diffs) == 1
        assert rhs_diffs[0].expected == 100.0
        assert rhs_diffs[0].actual == 999.0

    def test__compare_lp__constraint_coefficient_differs__reports_modified(self, tmp_path):
        # ARRANGE
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        coef_content = """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c1:
            +5 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", coef_content)

        # ACT
        diffs = compare_lp(expected, actual)

        # ASSERT
        coef_diffs = [
            d for d in diffs
            if d.category == "constraint" and d.diff_type == "modified"
            and "x" in d.detail and "c1" in d.detail
        ]
        assert len(coef_diffs) == 1
        assert coef_diffs[0].expected == 1.0
        assert coef_diffs[0].actual == 5.0


# ---------------------------------------------------------------------------
# Tolerance
# ---------------------------------------------------------------------------

class TestToleranceComparison:
    def test__compare_lp__coefficient_within_tolerance__no_diff_reported(self, tmp_path):
        # ARRANGE
        base = _write_lp(tmp_path, "base.lp", _BASE_LP)
        # Coefficient of x is 10.0; write 10.0 + 1e-10 which is within default tol
        near_content = """\
            \\* model *\\

            max
            obj:
            +10.0000000001 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        near = _write_lp(tmp_path, "near.lp", near_content)

        # ACT
        diffs = compare_lp(base, near)

        # ASSERT
        obj_coef_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
        assert obj_coef_diffs == []

    def test__compare_lp__coefficient_outside_tolerance__diff_reported(self, tmp_path):
        # ARRANGE
        base = _write_lp(tmp_path, "base.lp", _BASE_LP)
        # Coefficient of x is 10.0; write 10.0 + 1.0 which is outside default tol
        far_content = """\
            \\* model *\\

            max
            obj:
            +11 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        far = _write_lp(tmp_path, "far.lp", far_content)

        # ACT
        diffs = compare_lp(base, far)

        # ASSERT
        obj_coef_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
        assert len(obj_coef_diffs) == 1

    def test__compare_lp__custom_tolerance__applied_correctly(self, tmp_path):
        # ARRANGE
        base = _write_lp(tmp_path, "base.lp", _BASE_LP)
        # Coefficient of x is 10.0; write 10.5 which is within tolerance=1.0
        near_content = """\
            \\* model *\\

            max
            obj:
            +10.5 x
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        near = _write_lp(tmp_path, "near.lp", near_content)

        # ACT
        diffs = compare_lp(base, near, tolerance=1.0)

        # ASSERT
        obj_coef_diffs = [d for d in diffs if d.category == "objective" and d.diff_type == "modified"]
        assert obj_coef_diffs == []


# ---------------------------------------------------------------------------
# Fail-fast behaviour
# ---------------------------------------------------------------------------

class TestFailFast:
    def test__compare_lp__fail_fast_true__returns_at_most_one_diff(self, tmp_path):
        # ARRANGE — a file with multiple differences
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        many_diffs_content = """\
            \\* model *\\

            min
            obj:
            +99 x

            s.t.

            c1:
            +5 x
            <= 999

            bounds
               0 <= x <= 1
            binary
              x
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", many_diffs_content)

        # ACT
        diffs = compare_lp(expected, actual, fail_fast=True)

        # ASSERT
        assert len(diffs) == 1

    def test__compare_lp__fail_fast_false__returns_all_diffs(self, tmp_path):
        # ARRANGE — a file with multiple differences
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        many_diffs_content = """\
            \\* model *\\

            min
            obj:
            +99 x

            s.t.

            c1:
            +5 x
            <= 999

            bounds
               0 <= x <= 1
            binary
              x
            end
            """
        actual = _write_lp(tmp_path, "actual.lp", many_diffs_content)

        # ACT
        diffs = compare_lp(expected, actual, fail_fast=False)

        # ASSERT — must be more than one diff
        assert len(diffs) > 1


# ---------------------------------------------------------------------------
# Fail-fast per stage — exercises every early-return path in the comparer
# ---------------------------------------------------------------------------

# LP with same metadata as _BASE_LP but only variable x (y removed everywhere)
_LP_ONE_VAR = """\
    \\* model *\\

    max
    obj:
    +10 x

    s.t.

    c1:
    +1 x
    <= 100

    bounds
       0 <= x <= 1
    binary
      x
    end
    """

# LP with an extra variable z added everywhere
_LP_EXTRA_VAR = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y
    +5 z

    s.t.

    c1:
    +1 x
    +2 y
    +1 z
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
       0 <= z <= 1
    binary
      x
      y
      z
    end
    """

# LP with same variables as _BASE_LP but x declared as integer instead of binary
_LP_TYPE_CHANGE = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 10
       0 <= y <= 1
    general
      x
    binary
      y
    end
    """

# LP with same vars but different objective coefficient
_LP_OBJ_COEF_DIFF = """\
    \\* model *\\

    max
    obj:
    +99 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with y removed from objective only (vars/constraints keep y)
_LP_OBJ_MISSING_VAR = """\
    \\* model *\\

    max
    obj:
    +10 x

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with extra variable z in objective but z exists in both models' vars.
# The base _BASE_LP does not have z, so we need a pair for this test:
# expected = _LP_THREE_VARS_BASE, actual = _LP_OBJ_EXTRA_VAR_BODY
_LP_THREE_VARS_BASE = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
       0 <= z <= 1
    binary
      x
      y
      z
    end
    """

_LP_OBJ_EXTRA_VAR_BODY = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y
    +5 z

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
       0 <= z <= 1
    binary
      x
      y
      z
    end
    """

# LP with constraint c1 removed
_LP_NO_CONSTRAINT = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with an extra constraint c2
_LP_EXTRA_CONSTRAINT = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 100

    c2:
    +1 x
    <= 5

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with constraint sense changed (>= instead of <=)
_LP_CON_SENSE = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    >= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with constraint RHS changed
_LP_CON_RHS = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    <= 999

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with y removed from constraint (but kept in vars/obj)
_LP_CON_MISSING_VAR = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """

# LP with extra var z in constraint body; z exists in both models' vars.
# expected = _LP_THREE_VARS_BASE, actual = _LP_CON_EXTRA_VAR_BODY
_LP_CON_EXTRA_VAR_BODY = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +1 x
    +2 y
    +3 z
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
       0 <= z <= 1
    binary
      x
      y
      z
    end
    """

# LP with constraint coefficient changed
_LP_CON_COEF_DIFF = """\
    \\* model *\\

    max
    obj:
    +10 x
    +20 y

    s.t.

    c1:
    +5 x
    +2 y
    <= 100

    bounds
       0 <= x <= 1
       0 <= y <= 1
    binary
      x
      y
    end
    """


class TestFailFastPerStage:
    """Exercises every fail_fast early-return path in the comparer.

    Each test ensures the diff is detected and only one diff is returned,
    targeting a specific comparison stage so that the early-return inside
    that stage's helper function is the one that fires.
    """

    # -- Variable stage --

    def test__fail_fast__missing_variable__stops_at_variable_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_ONE_VAR)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "variable"
        assert diffs[0].diff_type == "missing"

    def test__fail_fast__extra_variable__stops_at_variable_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_EXTRA_VAR)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "variable"
        assert diffs[0].diff_type == "extra"

    def test__fail_fast__variable_type_change__stops_at_variable_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_TYPE_CHANGE)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "variable"
        assert diffs[0].diff_type == "modified"

    # -- Objective stage --

    def test__fail_fast__objective_coef_diff__stops_at_objective_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_OBJ_COEF_DIFF)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "objective"
        assert diffs[0].diff_type == "modified"

    def test__fail_fast__missing_var_in_objective__stops_at_objective_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_OBJ_MISSING_VAR)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "objective"
        assert diffs[0].diff_type == "missing"

    def test__fail_fast__extra_var_in_objective__stops_at_objective_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _LP_THREE_VARS_BASE)
        actual = _write_lp(tmp_path, "actual.lp", _LP_OBJ_EXTRA_VAR_BODY)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "objective"
        assert diffs[0].diff_type == "extra"

    def test__fail_fast__missing_objective__stops_at_objective_stage(self, tmp_path):
        # Two-objective expected vs one-objective actual
        two_obj = """\
            \\* model *\\

            max
            obj1:
            +10 x

            obj2:
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        one_obj = """\
            \\* model *\\

            max
            obj1:
            +10 x

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        expected = _write_lp(tmp_path, "expected.lp", two_obj)
        actual = _write_lp(tmp_path, "actual.lp", one_obj)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "objective"
        assert diffs[0].diff_type == "missing"

    def test__fail_fast__extra_objective__stops_at_objective_stage(self, tmp_path):
        one_obj = """\
            \\* model *\\

            max
            obj1:
            +10 x

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        two_obj = """\
            \\* model *\\

            max
            obj1:
            +10 x

            obj2:
            +20 y

            s.t.

            c1:
            +1 x
            +2 y
            <= 100

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """
        expected = _write_lp(tmp_path, "expected.lp", one_obj)
        actual = _write_lp(tmp_path, "actual.lp", two_obj)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "objective"
        assert diffs[0].diff_type == "extra"

    # -- Constraint stage --

    def test__fail_fast__missing_constraint__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_NO_CONSTRAINT)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "missing"

    def test__fail_fast__extra_constraint__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_EXTRA_CONSTRAINT)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "extra"

    def test__fail_fast__constraint_sense_changed__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_CON_SENSE)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "modified"
        assert "sense" in diffs[0].detail.lower()

    def test__fail_fast__constraint_rhs_changed__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_CON_RHS)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "modified"
        assert "rhs" in diffs[0].detail.lower()

    def test__fail_fast__missing_var_in_constraint__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_CON_MISSING_VAR)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "missing"

    def test__fail_fast__extra_var_in_constraint__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _LP_THREE_VARS_BASE)
        actual = _write_lp(tmp_path, "actual.lp", _LP_CON_EXTRA_VAR_BODY)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "extra"

    def test__fail_fast__constraint_coef_diff__stops_at_constraint_stage(self, tmp_path):
        expected = _write_lp(tmp_path, "expected.lp", _BASE_LP)
        actual = _write_lp(tmp_path, "actual.lp", _LP_CON_COEF_DIFF)

        diffs = compare_lp(expected, actual, fail_fast=True)

        assert len(diffs) == 1
        assert diffs[0].category == "constraint"
        assert diffs[0].diff_type == "modified"


# ---------------------------------------------------------------------------
# Order-agnostic comparison
# ---------------------------------------------------------------------------

class TestOrderAgnostic:
    def test__compare_lp__constraints_in_different_order__no_diff_reported(self, tmp_path):
        # ARRANGE — same constraints, different file order
        lp_a = _write_lp(tmp_path, "a.lp", """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c1:
            +1 x
            <= 50

            c2:
            +1 y
            <= 60

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """)
        lp_b = _write_lp(tmp_path, "b.lp", """\
            \\* model *\\

            max
            obj:
            +10 x
            +20 y

            s.t.

            c2:
            +1 y
            <= 60

            c1:
            +1 x
            <= 50

            bounds
               0 <= x <= 1
               0 <= y <= 1
            binary
              x
              y
            end
            """)

        # ACT
        diffs = compare_lp(lp_a, lp_b)

        # ASSERT
        assert diffs == []
