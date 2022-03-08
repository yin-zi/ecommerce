from django.urls import converters


class UsernameConverter:
	regex = '[a-zA-Z0-9_-]{5,20}'

	def to_python(self, value):
		return value

	def to_value(self, value):
		return value