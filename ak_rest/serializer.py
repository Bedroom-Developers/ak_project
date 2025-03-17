from rest_framework import serializers
from .models import CustomUser, Requests, Details, Items, RequestsItems
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'password']

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data['username'],
            role='User',
            fio='None',
            photo=None
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class WorkersSerializer(serializers.ModelSerializer):
    photo = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'role', 'password', 'fio', 'photo']
        extra_kwargs = {'password': {'write_only': True}}  # Чтобы пароль не отображался в ответе

    def get_photo(self, obj):
        return obj.photo.name if obj.photo else None  # Вернет только путь без домена

    def create(self, validated_data):
        photo = validated_data.pop('photo', None)
        user = CustomUser(
            username=validated_data['username'],
            role=validated_data['role'],
            fio=validated_data['fio']
        )
        user.set_password(validated_data['password'])
        if photo:
            user.photo = photo
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Аутентификация через username
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")

        # Получаем токен и добавляем данные
        token = self.get_token(user)
        return {
            'access': str(token.access_token),
            'refresh': str(token),
            'username': user.username,
            'role': user.role,
        }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['username'] = user.username
        token['role'] = user.role
        return token
    
class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requests
        fields = "__all__"

class DetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Details
        fields = "__all__"

class RequestItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestsItems
        fields = "__all__"

class PredictionSerializer(serializers.Serializer):
    worker_id = serializers.IntegerField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    price = serializers.IntegerField()
    window_type = serializers.CharField()

class ItemSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = Items
        fields = ['id', 'name', 'image', 'characteristics', 'category', 'description', 'count']

    def to_representation(self, instance):
        """Переопределяем представление данных, чтобы `image` хранился без домена."""
        data = super().to_representation(instance)
        if instance.image:
            data['image'] = instance.image.name  # Вернёт относительный путь без домена
        return data