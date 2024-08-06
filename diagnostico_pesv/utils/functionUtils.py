import unicodedata


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


def calculate_total_vehicles_quantities(data) -> int:
    total = 0
    for item in data:
        total += item.get("quantity_owned", 0)
        total += item.get("quantity_third_party", 0)
        total += item.get("quantity_arrended", 0)
        total += item.get("quantity_contractors", 0)
        total += item.get("quantity_intermediation", 0)
        total += item.get("quantity_leasing", 0)
        total += item.get("quantity_renting", 0)
    return total


def calculate_total_drivers_quantities(data) -> int:
    total = 0
    for item in data:
        total += item.get("quantity", 0)
    return total


def determine_company_size(dedication_id, total_vehicles, total_drivers):
    if dedication_id == 1:
        if (11 <= total_vehicles <= 19) or (2 <= total_drivers <= 19):
            return "BASICO"
        elif (20 <= total_vehicles <= 50) or (20 <= total_drivers <= 50):
            return "ESTANDAR"
        elif total_vehicles > 50 or total_drivers > 50:
            return "AVANZADO"
        else:
            raise ValueError(
                f"No se pudo determinar el tamaño de la organización para dedication_id={dedication_id} con total_vehicles={total_vehicles} y total_drivers={total_drivers}."
            )
    elif dedication_id == 2:
        if (11 <= total_vehicles <= 49) or (2 <= total_drivers <= 49):
            return "BASICO"
        elif (50 <= total_vehicles <= 100) or (50 <= total_drivers <= 100):
            return "ESTANDAR"
        elif total_vehicles > 100 or total_drivers > 100:
            return "AVANZADO"
        else:
            raise ValueError(
                f"No se pudo determinar el tamaño de la organización para dedication_id={dedication_id} con total_vehicles={total_vehicles} y total_drivers={total_drivers}."
            )
    else:
        raise ValueError(f"El valor de dedication_id={dedication_id} no es válido.")


def calculate_total_vehicles_quantities_for_company(vehicle_data):
    total_vehicles = 0
    for vehicle in vehicle_data:
        total_vehicles += (
            vehicle.get("quantity_owned", 0)
            + vehicle.get("quantity_third_party", 0)
            + vehicle.get("quantity_arrended", 0)
            + vehicle.get("quantity_contractors", 0)
            + vehicle.get("quantity_intermediation", 0)
            + vehicle.get("quantity_leasing", 0)
            + vehicle.get("quantity_renting", 0)
            + vehicle.get("quantity_employees", 0)
        )
    return total_vehicles


def calculate_total_drivers_quantities_for_company(driver_data):
    total_drivers = 0
    for driver in driver_data:
        total_drivers += driver.get("quantity", 0)
    return total_drivers


def eliminar_tildes(texto):
    # Normalizar el texto en forma NFD (Canonical Decomposition)
    nfkd_form = unicodedata.normalize("NFD", texto)
    # Filtrar los caracteres que no sean marcas diacríticas (Mn)
    return "".join([c for c in nfkd_form if not unicodedata.category(c) == "Mn"])
