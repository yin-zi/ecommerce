from django.shortcuts import render
from django.views import View


class ImageCodeView(View):
	def get(self, request, uuid):
		pass