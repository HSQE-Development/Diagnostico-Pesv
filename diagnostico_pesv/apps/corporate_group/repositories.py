from apps.corporate_group.models import Corporate
from .interfaces import ICorporateGroupRepository


class CorporateGroupRepository(ICorporateGroupRepository):
    def get_by_id(self, id: int):
        return Corporate.objects.filter(pk=id).first()

    def get_by_id_exist(self, id: int):
        return Corporate.objects.filter(pk=id).exists()
