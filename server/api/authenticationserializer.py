from rest_framework import serializers
from .models import User
from django.core.mail import send_mail
import random
import datetime
from django.utils import timezone
from bot.models import BotResponse
from bot.serializers import BotResponseSerializer
from user_profile.serializers import User_profile_serializer
from testimonials.serializers import testimonial_serializer
from django.template.loader import render_to_string
from django.utils.html import strip_tags

class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)
    otp = serializers.CharField(write_only=True, required=False)
    botresponse = BotResponseSerializer(many = True, read_only = True)
    user_profile = User_profile_serializer(many = True,read_only = True )
    review = testimonial_serializer(many= True, read_only = True)
    class Meta:
        model = User
        fields = [
            'name', 
            'email',
            'password', 
            'confirm_password', 
            'otp',
            'botresponse',
            'user_profile',
            'review', 
            ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)
        
        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        return data

    def create(self, validated_data):
        otp = str(random.randint(1000, 9999))
        validated_data['otp'] = otp
        validated_data['otp_expiration'] = datetime.datetime.now() + datetime.timedelta(minutes=10)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        # Render the HTML email content
        html_message = render_to_string('emails/otp_email.html', {'otp': otp})
        plain_message = strip_tags(html_message)

        # Send email with OTP
        send_mail(
            'Your OTP Code',
            plain_message,
            'nutriscanofficial@gmail.com',  # Replace with your email
            [validated_data['email']],
            fail_silently=False,
            html_message=html_message,
        )

        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
