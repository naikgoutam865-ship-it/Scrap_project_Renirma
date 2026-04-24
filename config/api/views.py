from rest_framework.decorators import api_view
from rest_framework.response import Response
from scrap.models import Scrap
from .serializers import ScrapSerializer


@api_view(['GET'])
def scrap_list(request):
    scraps = Scrap.objects.filter(is_available=True)
    serializer = ScrapSerializer(scraps, many=True)
    return Response(serializer.data)
