import platform

# Solo intenta importar pythoncom si el sistema operativo es Windows
if platform.system() == "Windows":
    try:
        import pythoncom

        pythoncom.CoInitialize()
    except Exception as e:
        print(f"Error al inicializar COM: {e}")
