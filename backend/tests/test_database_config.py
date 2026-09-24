import pytest

from backend.app.database import DatabaseConfigurationError, _get_postgres_url


@pytest.mark.parametrize(
    "scheme",
    ["postgres://", "postgresql://", "postgresql+psycopg://"],
)
def test_postgresql_urls_are_normalized_for_psycopg_in_development(
    monkeypatch: pytest.MonkeyPatch,
    scheme: str,
):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "DATABASE_URL",
        f"{scheme}lelaku_user:private-test-password@db.example.test:5432/lelaku",
    )

    url = _get_postgres_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "require"
    assert "private-test-password" not in url.render_as_string(hide_password=True)


@pytest.mark.parametrize("app_env", ["staging", "production", "prod"])
def test_non_development_environments_default_to_hostname_verifying_tls(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://lelaku_user:private-test-password@server.postgres.database.azure.com:5432/lelaku",
    )

    url = _get_postgres_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.query["sslmode"] == "verify-full"


def test_missing_app_environment_fails_closed_to_hostname_verifying_tls(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://lelaku_user:private-test-password@server.postgres.database.azure.com:5432/lelaku",
    )

    assert _get_postgres_url().query["sslmode"] == "verify-full"


def test_azure_url_preserves_full_verification_and_root_certificate(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://lelaku_user:private-test-password@server.postgres.database.azure.com:5432/lelaku"
        "?sslmode=verify-full&sslrootcert=%2Fetc%2Fssl%2Fazure-roots.pem",
    )

    url = _get_postgres_url()

    assert url.query["sslmode"] == "verify-full"
    assert url.query["sslrootcert"] == "/etc/ssl/azure-roots.pem"


@pytest.mark.parametrize("app_env", ["staging", "production"])
@pytest.mark.parametrize("sslmode", ["require", "verify-ca", "disable", "allow", "prefer"])
def test_staging_and_production_reject_tls_modes_without_full_host_verification(
    monkeypatch: pytest.MonkeyPatch,
    app_env: str,
    sslmode: str,
):
    monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:private-test-password@db.example.test/lelaku"
        f"?sslmode={sslmode}",
    )

    with pytest.raises(DatabaseConfigurationError, match="verify-full"):
        _get_postgres_url()


@pytest.mark.parametrize("sslmode", ["disable", "allow", "prefer"])
def test_remote_development_database_rejects_tls_downgrade_modes(
    monkeypatch: pytest.MonkeyPatch,
    sslmode: str,
):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql://user:private-test-password@db.example.test/lelaku?sslmode={sslmode}",
    )

    with pytest.raises(DatabaseConfigurationError, match="TLS"):
        _get_postgres_url()


def test_explicit_unencrypted_connection_is_limited_to_local_development(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost/lelaku?sslmode=disable")

    assert _get_postgres_url().query["sslmode"] == "disable"


@pytest.mark.parametrize(
    "database_url",
    [
        "",
        "not-a-database-url",
        "sqlite:///local.db",
        "mysql://user:pass@db/lelaku",
        "postgresql://",
        "postgresql://user:pass@db.example.test",
    ],
)
def test_missing_invalid_non_postgresql_or_incomplete_url_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    database_url: str,
):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", database_url)

    with pytest.raises(DatabaseConfigurationError) as error:
        _get_postgres_url()

    assert "private-test-password" not in str(error.value)
