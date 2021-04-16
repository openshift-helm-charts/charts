import pytest
from chartprreview.chartprreview import verify_user

def test_verify_user():
    with pytest.raises(SystemExit):
        verify_user("mbaiju", "partners", "test-org1", "test-chart")
