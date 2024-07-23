-- Crear el trigger en MySQL para convertir name a mayúsculas
DELIMITER //

CREATE TRIGGER arl_uppercase_name_trigger BEFORE INSERT ON arl_arl
FOR EACH ROW
BEGIN
    SET NEW.name = UPPER(NEW.name);
END;

//

DELIMITER;
-- Crear el trigger que llama a la función antes de insertar o actualizar
CREATE TRIGGER arl_uppercase_name_trigger BEFORE
INSERT
    OR
UPDATE ON arl_arl FOR EACH ROW
EXECUTE FUNCTION uppercase_name ();