from django.urls import path
from .views import ImageCodeview


urlpatterns = [
	path('image_code/<uuid>', ImageCodeview.as_view()),
]
