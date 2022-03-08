from django.urls import path

from . import views


app_name = 'captcha'
urlpatterns = [
	path('<uuid:captcha_uuid>', views.FormulaCaptchaView.as_view(), name='formula_captcha'),
]