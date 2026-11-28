"""Prototipo di cifratura a due fattori: frase segreta + impronta digitale.

DISATTIVATO per impostazione predefinita. Vedi GUIDA_ATTIVAZIONE.md.
"""

from .biometria import BiometriaNegata, BiometriaSimulata, FattoreBiometrico
from .cripto import (
    ErroreDecifratura,
    ErroreFormato,
    ParametriArgon2,
    cifra,
    decifra,
)
from .attivazione import Cassaforte, SistemaDisattivato

__all__ = [
    "BiometriaNegata",
    "BiometriaSimulata",
    "FattoreBiometrico",
    "ErroreDecifratura",
    "ErroreFormato",
    "ParametriArgon2",
    "cifra",
    "decifra",
    "Cassaforte",
    "SistemaDisattivato",
]
