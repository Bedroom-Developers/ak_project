from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)
from .views import (
    RegisterView,
    UserRequestView,
    GetRequestView,
    ManageDetailView,
    ManageMastersView,
    MasterGetDetailView,
    RequestItemsView,
    CustomTokenObtainPairView,
    GetItemsMasterView,
    ItemViewSet,
    WorkersRegisterView,
    GetMasterInfo,
    GetRequestMasterView,
    TrainModelView, 
    PredictCompletionDateView,
    TrainSuccessModelView,
    PredictSuccessView,
    )

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

urlpatterns = [
    path('user/requests/', UserRequestView.as_view(), name='user-requests'),  # Получить/создать запрос пользователя
    path('manager/requests/', GetRequestView.as_view(), name='get-requests'),  # Получить запросы для менеджера
    path('manager/details/', ManageDetailView.as_view(), name='manage-details'),  # Управление деталями заявок
    path('manager/masters/', ManageMastersView.as_view(), name='manage-masters'),  # Получить всех мастеров
    path('manager/get-master-info/', GetMasterInfo.as_view(), name='get-master-info'),
    path('master/details/', MasterGetDetailView.as_view(), name='master-get-details'),  # Получить детали для мастера
    path('master/request-items/', RequestItemsView.as_view(), name='master-request-items'),  # Запросить предметы на установку
    path('master/get-items/', GetItemsMasterView.as_view(), name='master-get-items'),
    path('master/get-request/', GetRequestMasterView.as_view(), name='master-get-request'),
    path('train-date-model/', TrainModelView.as_view(), name='train-date-model'),
    path('predict-date-time/', PredictCompletionDateView.as_view(), name='predict-time'),
    path('train-success/', TrainSuccessModelView.as_view(), name='train-success'),
    path('predict-success/', PredictSuccessView.as_view(), name='predict-success'),
    path('register/', RegisterView.as_view(), name='register'),
    path('worker-register/', WorkersRegisterView.as_view(), name='worker-register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls))
]