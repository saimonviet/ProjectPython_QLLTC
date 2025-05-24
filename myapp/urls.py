from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('yeu-cau-huy/<int:yc_id>/', views.huy_yeu_cau, name='huy_yeu_cau'),
    path('xem-yeu-caucau', views.xem_yeu_cau, name='xem_yeu_cau'),
    path('gui-yeu-cau/<int:lich_id>/', views.gui_yeu_cau_doi_lich, name='gui_yeu_cau'),
    path('yeu-cau-doi-lich', views.danh_sach_yeu_cau, name='danh_sach_yeu_cau'),
    path('duyet/<int:id>', views.duyet_yeu_cau, name='duyet_yeu_cau'),
    path('tu-choi/<int:id>/', views.tu_choi_yeu_cau, name='tu_choi_yeu_cau'),
    path('login', views.login_view, name='login'),
    path('register', views.register, name='register'),
    path('cap-nhat-lich/', views.cap_nhat_lich, name='cap_nhat_lich'),
    path("lich-su/<str:ma_kh>/<str:ma_vx>/", views.xem_lich_su_tiem, name="lich_su_tiem"),
    path("capnhat/<str:mavacxin>/", views.cap_nhat_vacxin, name="cap_nhat_vacxin"),
    path("them-khach-hang/", views.them_khach_hang, name="them_khach_hang"),
    path("khachhang/", views.view_khachhang, name="view_khachhang"),
    path("khachhang/xoa/<str:ma_kh>/", views.delete_khachhang, name="delete_khachhang"),
    path("them-vacxin/", views.them_vacxin, name="them_vacxin"),
    path('xem-lich-ad/', views.xem_lich_admin, name='xem_lich_admin'),
    path('xem-lich/', views.xem_lich, name='xem_lich'),
    path('tim-kiem-lich/', views.tim_kiem_lich, name='tim_kiem_lich'),
    path('', views.danh_sach_vacxin, name='index'),
    path('adminhome/', views.admin_home, name='admin_home'),
    path('cushome/', views.customer_home, name='customer_home'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('delete-vacxin/<str:ma_vx>/', views.delete_vacxin, name='delete_vacxin'),
    path('vacxin/', views.view_vacxin, name='view_vacxin'),
    path('<str:ma_vacxin>/', views.chi_tiet_vacxin, name='chi_tiet_vacxin'),
    path('customer/<str:ma_kh>/', views.chi_tiet_khach_hang, name='customer_detail'),
    path("dat-lich/<str:MaVacXin>/", views.dat_lich, name="dat_lich"),
    path('xoa-lich/<str:ma_kh>/<str:ma_vx>/', views.xoa_lich, name='xoa_lich'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
