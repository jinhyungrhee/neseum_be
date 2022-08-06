from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from allauth.account.adapter import get_adapter
from django.utils.translation import gettext_lazy as _

class CustomRegisterSerializer(RegisterSerializer):

  def validate_username(self, username):
        codes = ['사과', '오이', '호박', '당근' , '시금치', '열무' , '토란', '감자', '브로콜리', '양배추'] # 30명 코드
        username = get_adapter().clean_username(username)
        if username not in codes:
          raise serializers.ValidationError(_("올바른 코드를 입력하세요!"))
        return username