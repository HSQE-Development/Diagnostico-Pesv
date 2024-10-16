"""
    Este archivo se declaran las constantes como por ejemplo IDs de las relaciones para no poner numeros magicos
    Ejemplo:
    Company.objects.filter(arl=1) --> esto estaria mal ya que podemos confundirnos al intentar saber que arl es 1

    En cambio hacer

    Company.objects.filter(arl=CONSTANTE_DE_ARL_CON_ID_1)
"""

from enum import Enum


class ComplianceIds(Enum):
    CUMPLE = 1
    NO_CUMPLE = 2
    CUMPLE_PARCIALMENTE = 3
    NO_APLICA = 4


class CompanySizeEnum(Enum):
    AVANZADO = 3
    ESTANDAR = 2
    BASICO = 1
