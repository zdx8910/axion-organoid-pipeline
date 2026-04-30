from io import StringIO
from pathlib import Path

import pytest

from meaorganoid.errors import MEASchemaError
from meaorganoid.io import canonical_columns, read_axion_spike_csv

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures"


@pytest.mark.parametrize(
    "fixture_name",
    [
        "axion_minimal.csv",
        "axion_aliases_timestamp.csv",
        "axion_aliases_spiketime.csv",
        "axion_aliases_underscore.csv",
    ],
)
def test_alias_fixtures_have_canonical_columns_and_row_count(fixture_name: str) -> None:
    result = read_axion_spike_csv(FIXTURE_DIR / fixture_name)

    assert tuple(result.columns[:3]) == canonical_columns()
    assert len(result) == 30
    assert str(result["time_s"].dtype) == "float64"


def test_extra_whitespace_headers_parse_successfully() -> None:
    result = read_axion_spike_csv(FIXTURE_DIR / "axion_extra_whitespace.csv")

    assert tuple(result.columns[:3]) == canonical_columns()
    assert len(result) == 30


def test_missing_time_alias_error_mentions_path_and_seen_columns() -> None:
    path = FIXTURE_DIR / "axion_missing_time.csv"

    with pytest.raises(MEASchemaError) as error:
        read_axion_spike_csv(path)

    message = str(error.value)
    assert str(path) in message
    assert "columns seen:" in message


def test_axion_electrode_labels_infer_well() -> None:
    csv = StringIO("Time (s),Electrode\n0.1,A1_11\n0.2,A1_12\n")
    csv.name = "infer_well.csv"

    result = read_axion_spike_csv(csv)

    assert result["well"].tolist() == ["A1", "A1"]


def test_mixed_electrode_labels_leave_empty_well_and_warn(caplog: pytest.LogCaptureFixture) -> None:
    csv = StringIO("Time (s),Electrode\n0.1,A1_11\n0.2,weird_label\n")
    csv.name = "mixed_labels.csv"

    with caplog.at_level("WARNING", logger="meaorganoid.io"):
        result = read_axion_spike_csv(csv)

    assert result["well"].tolist() == ["", ""]
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "WARNING"
