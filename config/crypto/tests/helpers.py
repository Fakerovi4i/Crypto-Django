from unittest.mock import MagicMock


def make_mock_provider(*, symbol_exists: bool = True) -> MagicMock:
    mock_provider = MagicMock()
    mock_provider.__enter__.return_value = mock_provider
    mock_provider.symbol_exists.return_value = symbol_exists
    return mock_provider