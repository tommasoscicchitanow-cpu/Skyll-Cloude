"""Le prove non dipendono dall'interruttore locale del PC: anche dove il
sistema è acceso (configurazione.locale.json), qui risulta spento, salvo le
prove che passano un file di configurazione esplicito."""

import pytest


@pytest.fixture(autouse=True)
def _interruttore_spento(monkeypatch, tmp_path_factory):
    from protezione_acutis import attivazione

    monkeypatch.setattr(attivazione, "CONFIGURAZIONE_PREDEFINITA",
                        tmp_path_factory.mktemp("config") / "inesistente.json")
