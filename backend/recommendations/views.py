from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Recommendation, Dealer
from .serializers import RecommendationSerializer, DealerSerializer
from django.db.models import F
from math import radians, cos, sin, asin, sqrt

class RecommendationByDiseaseView(APIView):
    def get(self, request, disease_code):
        recs = Recommendation.objects.filter(disease_code__iexact=disease_code, published=True).order_by('-version')
        if not recs.exists():
            return Response({"message":"No published recommendation for this disease"}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecommendationSerializer(recs.first())
        return Response(serializer.data)

# Simple Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    # degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2*asin(sqrt(a))
    r = 6371 # km
    return c * r

class NearbyDealersView(APIView):
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = float(request.query_params.get('radius', 50))
        dealer_type = request.query_params.get('type')  # e.g., agrovet

        if not lat or not lng:
            return Response({"message":"lat and lng required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lat = float(lat); lng = float(lng)
        except ValueError:
            return Response({"message":"invalid lat/lng"}, status=status.HTTP_400_BAD_REQUEST)

        qs = Dealer.objects.all()
        if dealer_type:
            qs = qs.filter(type=dealer_type)

        nearby = []
        for d in qs:
            if d.latitude is None or d.longitude is None:
                continue
            dist = haversine(lat,lng,d.latitude,d.longitude)
            if dist <= radius_km:
                data = DealerSerializer(d).data
                data['_distance_km'] = round(dist,2)
                nearby.append(data)
        # sort by distance
        nearby.sort(key=lambda x: x['_distance_km'])
        return Response(nearby)
