from rest_framework import serializers
from .models import Company, Segments


class SegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Segments,
        fields = [
            'id',
            'name'
        ]

class UserDetailSerializer(serializers.ModelSerializer):
    segment = serializers.PrimaryKeyRelatedField(queryset=Segments.objects.all(), write_only=True)
    segment_detail = SegmentSerializer(source='segment', read_only=True)
    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'nit',
            'size',
            'segment',
            'segment_detail',
            'dependant',
            'dependant_phone',
            'activities_ciiu',
            'email',
            'acquired_certification',
            'diagnosis',
        ]