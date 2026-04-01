from app.core.config import Settings


def test_settings_parse_csv_lists(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://budget.example.com, http://localhost")
    monkeypatch.setenv("ALLOWED_EXTENSIONS", "jpg,png,pdf")

    settings = Settings()

    assert settings.allowed_origins_list == ["https://budget.example.com", "http://localhost"]
    assert settings.allowed_extensions_list == ["jpg", "png", "pdf"]


