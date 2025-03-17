from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count, Avg, F
from django.utils.timezone import now
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib 
from datetime import datetime
from rest_framework import status
from .models import Requests, RequestsItems, Reviews, Items, Details, Features, CustomUser
from .ml_model import train_model, predict_completion_date, train_success_model, predict_success
from .serializer import UserSerializer, CustomTokenObtainPairSerializer, RequestSerializer, DetailSerializer, RequestItemSerializer, ItemSerializer, WorkersSerializer, PredictionSerializer
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser

class IsAdminUserRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'
    
class IsAdminOrManagerRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin' or request.user.role == 'manager'

class IsAdminOrMasterRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin' or request.user.role == 'master'

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkersRegisterView(APIView):
    permission_classes = [IsAdminUserRole]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = WorkersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def check_role(request, required_role):
    role = request.user.role

    if role != required_role:
        return Response({'error': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
    return None

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = {
            'phone': request.data.get('phone', None),
            'address': request.data.get('address', None),
            'user_id': request.user.id,
            'window_type': request.data.get('window_type', None),
            'width': request.data.get('width', None),
            'height': request.data.get('height', None),
            'window_image': request.data.get('window_image', None),
        }

        if not data['phone'] or not data['address'] or not data['height'] or not data['window_type'] or not data['width'] or not data['window_image']:
            return Response({'error': 'Parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        price = int(data['window_type']) * int(data['width']) * int(data['height'])
        data['price'] = price

        serializer = RequestSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': f'Success {serializer.data}'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'Fail'}, status=status.HTTP_409_CONFLICT)
    
    def get(self, request, *args, **kwargs):
        data = Requests.objects.filter(user_id = request.user)
        serializer = RequestSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class GetRequestView(APIView):
    permission_classes = [IsAdminOrManagerRole]

    def get(self, request, *args, **kwargs):

        data = Requests.objects.filter(status = 'Not accepted')
        serializer = RequestSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ManageDetailView(APIView):
    permission_classes = [IsAdminOrManagerRole]

    def post(self, request, *args, **kwargs):
        
        data = {
            "request_id": request.data.get('request_id'),
            "worker_id": request.data.get('worker_id')
        }

        serializer = DetailSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            request_object = Requests.objects.get(id = data['request_id'])
            request_object.status = 'Accepted'
            request_object.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Fail'}, status=status.HTTP_409_CONFLICT)
    
    def get(self, request, *args, **kwargs):

        data = Details.objects.all()
        serializer = DetailSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ManageMastersView(APIView):
    permission_classes = [IsAdminOrManagerRole]

    def get(self, request, *args, **kwargs):
        
        data = CustomUser.objects.filter(role = "master")
        serializer = WorkersSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MasterGetDetailView(APIView):
    permission_classes = [IsAdminOrMasterRole]

    def get(self, request, *args, **kwargs):
        data = Details.objects.filter(worker_id = request.user)
        serializer = DetailSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, *args, **kwargs):
        detail_id = request.query_params.get("detail_id", None)

        if not detail_id or not detail_id.isdigit():
            return Response({'error': 'detail_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        detail_object = get_object_or_404(Details, id=detail_id, worker_id=request.user)
        detail_object.status = "Done"
        detail_object.measurement_date = datetime.now()
        detail_object.save()
        request_object = get_object_or_404(Requests, id = detail_object.request_id.id)
        request_object.status = "Done"
        request_object.updated_at = datetime.now()
        request_object.save()
        return Response({'message': 'Success'}, status=status.HTTP_200_OK)
    
class RequestItemsView(APIView):
    permission_classes = [IsAdminOrMasterRole]

    def post(self, request, *args, **kwargs):
        
        data = {
            "detail_id": request.data.get('detail_id', None),
            "item_id": request.data.get('item_id', None),
            "installation_date": request.data.get('installation_date', None),
            "count": request.data.get('count', None)
        }
        item_object = Items.objects.get(id = data['item_id'])
        item_object.count = item_object.count - int(data['count'])
        item_object.save()

        serializer = RequestItemSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Fail'}, status=status.HTTP_409_CONFLICT)
    
    def get(self, request, *args, **kwargs):
        
        detail_id = request.query_params.get('detail_id', None)
        if not detail_id:
            return Response({'error': 'Parameter'}, status=status.HTTP_400_BAD_REQUEST)

        data = RequestsItems.objects.filter(detail_id = int(detail_id))
        serializer = RequestItemSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetRequestMasterView(APIView):
    permission_classes = [IsAdminOrMasterRole]

    def get(self, request, *args, **kwargs):
        request_id = request.query_params.get('request_id', None)

        if not request_id:
            return Response({'error': 'request_id is required!'}, status=status.HTTP_400_BAD_REQUEST)
        
        data = Requests.objects.get(id = request_id)
        serializer = RequestSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetItemsMasterView(APIView):
    permission_classes = [IsAdminOrMasterRole]

    def get(self, request, *args, **kwargs):
        
        data = Items.objects.all()
        serializer = ItemSerializer(data, many = True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Items.objects.all()
    serializer_class = ItemSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAdminUserRole]

class GetMasterInfo(APIView):
    permission_classes = [IsAdminOrManagerRole]

    def get(self, request, *args, **kwargs):
        worker_id = request.query_params.get('worker_id', None)

        if not worker_id:
            return Response({'error': 'worker_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        worker_data = CustomUser.objects.get(id = worker_id)
        worker_details = Details.objects.filter(worker_id=worker_id)

        worker_details_count = worker_details.count()
        worker_details_done_count = worker_details.filter(status='Done').count()
        worker_details_waiting_count = worker_details.filter(status='Waiting').count()

        worker_detail_ids = worker_details.values_list('id', flat=True)

        worker_requested_items = (
            RequestsItems.objects.filter(detail_id__in=worker_detail_ids).count()
            if worker_detail_ids else 0
        )

        response_data = {
            "worker_id": worker_data.id,
            "worker_username": worker_data.username,
            "worker_role": worker_data.role,
            "worker_fio": worker_data.fio,
            "worker_photo": request.build_absolute_uri(worker_data.photo.url) if worker_data.photo else None,
            "total_details": worker_details_count,
            "completed_details": worker_details_done_count,
            "waiting_details": worker_details_waiting_count,
            "total_requested_items": worker_requested_items
        }

        return Response(response_data, status=200)


class TrainModelView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request):
        result = train_model()
        return Response({'message': result}, status=status.HTTP_200_OK)

class PredictCompletionDateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request_id = request.data.get("request_id")
        if not request_id:
            return Response({'error': 'Не указан request_id'}, status=status.HTTP_400_BAD_REQUEST)
        
        result = predict_completion_date(request_id)
        return Response(result, status=status.HTTP_200_OK)
    
class TrainSuccessModelView(APIView):
    permission_classes = [IsAdminUserRole]
    """Запуск обучения модели успеха заказа"""

    def post(self, request):
        try:
            train_success_model()
            return Response({"message": "Модель обучена"}, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PredictSuccessView(APIView):
    permission_classes = [IsAdminOrManagerRole]
    """Предсказание успеха заказа"""

    def post(self, request):
        serializer = PredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            prediction = predict_success(**data)
            return Response(prediction, status=status.HTTP_200_OK)
        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)