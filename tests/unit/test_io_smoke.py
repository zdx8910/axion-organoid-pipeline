from io import StringIO

import pytest

from meaorganoid.errors import MEASchemaError
from meaorganoid.io import read_axion_spike_csv


def test_read_axion_spike_csv_accepts_time_aliases() -> None:
    for alias in ["Time (s)", "Time", "Timestamp", "Spike Time", "SpikeTime", "time_s"]:
        csv = StringIO(f"{alias},Electrode,Well\n0.1,E1,A1\n0.2,E1,A1\n")
        csv.name = f"in_memory_{alias}.csv"

        result = read_axion_spike_csv(csv)

        assert ["time_s", "electrode", "well"] == list(result.columns)
        assert result["time_s"].tolist() == [0.1, 0.2]
        assert result["electrode"].tolist() == ["E1", "E1"]
        assert result["well"].tolist() == ["A1", "A1"]


def test_read_axion_spike_csv_missing_time_column_mentions_file_path() -> None:
    csv = StringIO("Electrode,Well\nE1,A1\n")
    csv.name = "missing_time.csv"

    with pytest.raises(MEASchemaError, match=r"missing_time\.csv"):
        read_axion_spike_csv(csv)
