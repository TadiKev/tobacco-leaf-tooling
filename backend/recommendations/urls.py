from django.urls import path
from .views import RecommendationByDiseaseView, NearbyDealersView

urlpatterns = [
    path('recommendations/<str:disease_code>/', RecommendationByDiseaseView.as_view(), name='recommendation-by-disease'),
    path('dealers/nearby/', NearbyDealersView.as_view(), name='nearby-dealers'),
]
