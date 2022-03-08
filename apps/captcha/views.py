from django.shortcuts import render, HttpResponse
from django.views.generic import View
from django_redis import get_redis_connection

from utils.captcha import generate_formula_captcha


class FormulaCaptchaView(View):

	def get(self, request, captcha_uuid):
		captcha_text, captcha_ans, captcha_im = generate_formula_captcha()
		redis_cli = get_redis_connection('captcha')
		redis_cli.setex(str(captcha_uuid), 300, captcha_ans)  # 300s过期
		return HttpResponse(captcha_im, content_type='image/png')
