from rest_framework import serializers
from .models import Recommendation, Treatment, Dealer

class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ['id','type','name','active_ingredient','dose_text','application_method','pre_harvest_interval','ppe','notes','source']

class RecommendationSerializer(serializers.ModelSerializer):
    treatments = TreatmentSerializer(many=True, read_only=True)
    class Meta:
        model = Recommendation
        fields = ['id','disease_code','title','severity','nonchem_recommendations','treatments','version','approved_by','approved_at','published','safety_flag','tags','last_updated']

class DealerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dealer
        fields = '__all__'
