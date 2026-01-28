from django.contrib import admin
from .models import Recommendation, Treatment, Dealer

class TreatmentInline(admin.TabularInline):
    model = Treatment
    extra = 0

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('title','disease_code','version','published','approved_by','approved_at')
    list_filter = ('published','severity','safety_flag')
    search_fields = ('title','disease_code','tags')
    inlines = [TreatmentInline]

@admin.register(Dealer)
class DealerAdmin(admin.ModelAdmin):
    list_display = ('name','type','city','province','contact_phone')
    search_fields = ('name','city','inventory_tags')
