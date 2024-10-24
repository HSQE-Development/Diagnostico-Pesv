class ArlServices:
    @staticmethod
    def has_no_active_diagnosis_company(arl_instance):
        from apps.diagnosis.models import Diagnosis

        # Verificar si existen Companies asociadas a esta ARL donde deleted_at es NULL
        active_count = Diagnosis.objects.filter(
            company__arl=arl_instance, deleted_at__isnull=True
        ).count()
        # Retornar True si no hay Companies activas, de lo contrario False
        return active_count == 0
