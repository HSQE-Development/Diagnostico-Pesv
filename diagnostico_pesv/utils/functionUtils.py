def blank_to_null(data: str):
    """
    Transforma valores en blanco a None.

    Parameters:
    data (str): El valor a verificar.

    Returns:
    None or str: Retorna None si el valor está en blanco, de lo contrario retorna el valor original.
    """
    if data == "" or data is None:
        return None
    return data
