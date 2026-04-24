from rest_framework import serializers
from scrap.models import Scrap


class ScrapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scrap
        fields = '__all__'
