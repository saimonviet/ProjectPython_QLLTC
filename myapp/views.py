from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import UserRole, VacXin, KhachHang, Lich, YeuCauDoiLich
from datetime import datetime, timedelta, date
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Max
from django.db.models import Q  
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import os
import re
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.utils.dateparse import parse_date

def login_view(request):
    # Kiểm tra nếu người dùng đã đăng nhập thì không cần vào trang đăng nhập nữa
    if request.session.get('username'):
        role = request.session.get('role', '').lower()
        if role == 'admin':
            return redirect(reverse('admin_home'))
        elif role == 'customer':
            return redirect(reverse('customer_home'))

    if request.method == "POST":
        username = request.POST.get('username', '').strip().lower()  
        password = request.POST.get('password', '').strip()
        
        try:
            user = UserRole.objects.get(username=username)
        
            if password == user.password:  # Chưa có mã hóa mật khẩu
                request.session['username'] = user.username
                request.session['MaKH'] = user.MaKH
                request.session['role'] = user.role.lower()
                request.session.modified = True  # Đảm bảo session được cập nhật

                role = user.role.lower()
                if role == 'admin':
                    return redirect(reverse('admin_home'))
                elif role == 'customer':
                    return redirect(reverse('customer_home'))
                else:
                    return render(request, 'login.html', {'errorMessage': "Vai trò không hợp lệ."})
            else:
                return render(request, 'login.html', {'errorMessage': "Sai tài khoản hoặc mật khẩu."})

        except UserRole.DoesNotExist:
            return render(request, 'login.html', {'errorMessage': "Sai tài khoản hoặc mật khẩu!"})

    return render(request, 'login.html')

def generate_new_makh():
    last_kh = KhachHang.objects.aggregate(Max('ma_kh'))['ma_kh__max']
    if last_kh:
        prefix = ''.join(filter(str.isalpha, last_kh))
        number = ''.join(filter(str.isdigit, last_kh))
        new_number = str(int(number) + 1).zfill(len(number))
        return prefix + new_number
    else:
        return 'KH001'

@csrf_exempt
def register(request):
    if request.method == 'POST':
        fullname = request.POST.get('fullname')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Kiểm tra số điện thoại đủ 10 chữ số
        if len(phone) != 10 or not phone.isdigit():
            return HttpResponse("<script>alert('Số điện thoại phải gồm đúng 10 chữ số!'); window.history.back();</script>")

        # Kiểm tra username đã tồn tại chưa
        if UserRole.objects.filter(username=username).exists():
            return HttpResponse("<script>alert('Tên đăng nhập đã tồn tại!'); window.history.back();</script>")

        # Kiểm tra số điện thoại đã tồn tại chưa
        if KhachHang.objects.filter(so_dien_thoai=phone).exists():
            return HttpResponse("<script>alert('Số điện thoại đã được sử dụng!'); window.history.back();</script>")

        # Sinh mã khách hàng mới
        ma_kh = generate_new_makh()

        # Tạo khách hàng
        kh = KhachHang.objects.create(
            ma_kh=ma_kh,
            ho_ten=fullname,
            so_dien_thoai=phone,
            dia_chi=address,
            ngay_sinh=dob,
            gioi_tinh=gender
        )

        # Tạo tài khoản người dùng
        UserRole.objects.create(
            username=username,
            password=password,
            MaKH=ma_kh,
            role='customer'
        )
       # Thông báo và chuyển hướng
        return HttpResponse("""
            <script>
                alert("Đăng ký thành công! Vui lòng đăng nhập để sử dụng !");
                window.location.href = "/login"; 
            </script>
        """)
    return render(request, 'register.html')

def admin_home(request):
    if not request.session.get('username'):
        return redirect('login')

    if request.session.get('role', '').lower() != 'admin':
        return redirect('customer_home')

    username = request.session['username']
    listLich = Lich.objects.select_related('ma_kh').all()

    return render(request, 'adminhome.html', {
        'username': username,
        'listLich': listLich
    })

def customer_home(request):
    if not request.session.get('username'):
        return redirect('login')

    role = request.session.get('role', '').lower()

    if role == 'admin':
        return redirect('admin_home')

    if role == 'customer':
        try:
            ma_kh = request.session.get('MaKH')
            if not ma_kh:
                return redirect('login')

            kh = KhachHang.objects.get(ma_kh=ma_kh)
            
            ngay_hien_tai = date.today()
            ba_ngay_sau = ngay_hien_tai + timedelta(days=3)

            # Lấy lịch tiêm từ hôm nay đến 3 ngày tới
            lich_tiem_sap_toi = Lich.objects.filter(
                trangthai=False,
                ma_kh=ma_kh,
                tg_tiem__gte=ngay_hien_tai,
                tg_tiem__lte=ba_ngay_sau
            ).order_by('tg_tiem')

            return render(request, 'cushome.html', {
                'kh': kh,
                'lich_tiem': lich_tiem_sap_toi,
            })

        except KhachHang.DoesNotExist:
            return HttpResponse("Không tìm thấy khách hàng.")
        except Exception as e:
            return HttpResponse(f"Lỗi xảy ra: {str(e)}")

    return redirect('login')

def logout_view(request):
    request.session.flush()
    return redirect(reverse('login')) # Chuyển về trang đăng nhập

def danh_sach_vacxin(request):
    query = request.GET.get('search', '')
    if query:
        vacxins = VacXin.objects.filter(TenVacXin__icontains=query)
    else:
        vacxins = VacXin.objects.all()

    return render(request, 'index.html', {'vacxins': vacxins})

def chi_tiet_vacxin(request, ma_vacxin):
    vacxin = get_object_or_404(VacXin, MaVacXin=ma_vacxin)
    return render(request, 'vacxindetail.html', {'vacxin': vacxin})

def change_password(request):
    if "username" not in request.session or request.session.get("role") != "customer":
        return redirect("login")  # Điều hướng đến trang đăng nhập nếu chưa đăng nhập

    if request.method == "POST":
        current_password = request.POST.get("currentPassword")
        new_password = request.POST.get("newPassword")
        confirm_password = request.POST.get("confirmPassword")

        username = request.session["username"]
        user = UserRole.objects.filter(username=username).first()

        if user and current_password == user.password:  # So sánh trực tiếp mật khẩu cũ
            if new_password == confirm_password:
                user.password = new_password  # Lưu trực tiếp mật khẩu mới (không mã hóa)
                user.save()
                # Thông báo và chuyển hướng
                return HttpResponse("""
                    <script>
                        alert("Đổi mật khẩu thành công !");
                        window.location.href = "/cushome"; 
                    </script>
                """)
            else:
                messages.error(request, "Mật khẩu xác nhận không khớp.")
        else:
            messages.error(request, "Mật khẩu hiện tại không đúng.")

    return render(request, "change_password.html")

def chi_tiet_khach_hang(request, ma_kh):
    kh = KhachHang.objects.get(ma_kh=ma_kh)

    if request.method == "POST":
        kh.ho_ten = request.POST.get("hotenkh")
        kh.so_dien_thoai = request.POST.get("sodienthoai")
        kh.dia_chi = request.POST.get("diachi")
        kh.ngay_sinh = request.POST.get("ngaysinh")
        kh.gioi_tinh = request.POST.get("gioitinh")
        kh.save()
        return redirect("customer_home")  # Điều hướng về trang chủ khách hàng sau khi cập nhật thành công

    return render(request, "thong_tin_kh.html", {"kh": kh})

def view_vacxin(request):
    role = request.session.get('role')

    search_query = request.POST.get('search', '')
    if search_query:
        listVX = VacXin.objects.filter(TenVacXin__icontains=search_query)
    else:
        listVX = VacXin.objects.all()
    if role == "admin":
        return render(request, 'view_vacxin_admin.html', {'listVX': listVX})
    else:
        return render(request, 'view_vacxin.html', {'listVX': listVX})

def xem_lich(request):
    username = request.session.get('username')  # Lấy username từ session
    MaKH = request.session['MaKH']
    if not username:  # Kiểm tra nếu chưa có username trong session
        return redirect('login')  # Chuyển hướng về trang login hoặc báo lỗi
    
    listLich = Lich.objects.filter(ma_kh=MaKH)

    return render(request, 'view_history.html', {'listLich': listLich})

def xem_lich_admin(request):
    role = request.session.get('role')
    if role == "customer":
        return redirect('xem_lich')

    ma_kh = request.GET.get('ma_kh', '')
    ma_vx = request.GET.get('ma_vx', '')

    listLich = Lich.objects.filter(stt_mui=1)
    if ma_kh:
        listLich = listLich.filter(ma_kh__ma_kh__icontains=ma_kh)
    if ma_vx:
        listLich = listLich.filter(ma_vx__icontains=ma_vx)

    return render(request, 'view_admin_history.html', {'listLich': listLich})


def xoa_lich(request, ma_kh, ma_vx):
    role = request.session.get('role')
    if role == "admin":
        Lich.objects.filter(ma_kh=ma_kh, ma_vx=ma_vx).delete()
        return redirect('xem_lich_admin')
    else: 
        return redirect('xem_lich')

def tim_kiem_lich(request):
    username = request.session.get('username')  # Lấy username từ session
    MaKH = request.session['MaKH']
    if not username:  # Kiểm tra nếu chưa có username trong session
        return redirect('login')  # Chuyển hướng về trang login hoặc báo lỗi

    search_date = request.POST.get('TGTiem')  

    if search_date:
        list_lich = Lich.objects.filter(ma_kh=MaKH, tg_tiem=search_date)
    else:
        list_lich = Lich.objects.filter(ma_kh=MaKH)

    return render(request, 'view_history.html', {'listLich': list_lich})

def dat_lich(request, MaVacXin):
    user = request.session.get('username')
    role = request.session.get('role')

    if role != "customer":
        return redirect('login')
    
    vacxin = get_object_or_404(VacXin, MaVacXin=MaVacXin)

    # Kiểm tra đã đăng ký chưa
    MaKH = request.session['MaKH']
    if Lich.objects.filter(ma_kh=MaKH, ma_vx=MaVacXin).exists():
        listVX = VacXin.objects.all()
        return render(request, 'view_vacxin.html', {
            'listVX': listVX,
            'message': 'Bạn đã đăng ký tiêm vaccine này rồi!'
        })

    if request.method == 'POST':
        ngay_tiem = request.POST.get('ngaytiem')
        try:
            ngay_tiem = datetime.strptime(ngay_tiem, '%Y-%m-%d').date()
            if ngay_tiem <= date.today():
                return render(request, 'dat_lich.html', {
                    'vacxin': vacxin,
                    'message': 'Ngày tiêm phải là ngày trong tương lai!'
                })
        except ValueError:
            return render(request, 'dat_lich.html', {
                'vacxin': vacxin,
                'message': 'Ngày tiêm không hợp lệ!'
            })
        # Lấy toàn bộ lịch tiêm của khách hàng hiện tại
        lich_hien_tai = Lich.objects.filter(ma_kh=MaKH).values_list('tg_tiem', flat=True)

        # Kiểm tra từng mũi
        ngay_tiem_copy = ngay_tiem
        for i in range(vacxin.SoMui):
            if ngay_tiem_copy in lich_hien_tai:
                return render(request, 'dat_lich.html', {
                    'vacxin': vacxin,
                    'message': f'Ngày {ngay_tiem_copy.strftime("%d/%m/%Y")} đã có lịch tiêm khác! Vui lòng chọn ngày khác.'
                })
            ngay_tiem_copy += timedelta(days=30)

        # Nếu không trùng, tiến hành tạo lịch
        for i in range(vacxin.SoMui):
            Lich.objects.create(
                ma_kh=MaKH,
                ma_vx=MaVacXin,
                ten_vx=vacxin.TenVacXin,
                stt_mui=i + 1,
                tg_tiem=ngay_tiem,
                trangthai=False
            )
            ngay_tiem += timedelta(days=30)

        return redirect('xem_lich')

    return render(request, 'dat_lich.html', {'vacxin': vacxin})

def generate_next_vacxin_code():
    last_vaccine = VacXin.objects.order_by('-MaVacXin').first()
    if last_vaccine:
        match = re.match(r'^VX(\d+)$', last_vaccine.MaVacXin)
        if match:
            next_number = int(match.group(1)) + 1
            return f"VX{next_number:03d}"
    return "VX001"

def them_vacxin(request):
    if request.method == "POST":
        ten_vacxin = request.POST.get("TenVacXin")
        so_mui = request.POST.get("SoMui")
        mota = request.POST.get("Mota")
        gia_vacxin = request.POST.get("GiaVacXin")
        ten_hang = request.POST.get("TenHangSX")
        hinh_anh_file = request.FILES.get("HinhAnh")
        ma_vacxin = generate_next_vacxin_code()

        try:
            static_image_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'images')
            os.makedirs(static_image_path, exist_ok=True)

            filename = hinh_anh_file.name
            save_path = os.path.join(static_image_path, filename)

            with open(save_path, 'wb+') as f:
                for chunk in hinh_anh_file.chunks():
                    f.write(chunk)

            relative_image_path = f"images/{filename}"

            vacxin = VacXin(
                MaVacXin=ma_vacxin,
                TenVacXin=ten_vacxin,
                SoMui=so_mui,
                Mota=mota,
                GiaVacXin=gia_vacxin,
                TenHangSX=ten_hang,
                HinhAnh=relative_image_path
            )
            vacxin.save()

            messages.success(request, f"Đã thêm vaccine {ma_vacxin} thành công!")
            return redirect("them_vacxin")

        except Exception as e:
            messages.error(request, f"Lỗi: {e}")
            return redirect("them_vacxin")

    return render(request, "them_vacxin.html", {
        "ma_tiep_theo": generate_next_vacxin_code()
    })

def delete_vacxin(request, ma_vx):
    if request.method == "POST":
        vacxin = get_object_or_404(VacXin, MaVacXin=ma_vx)
        
        # Xóa tất cả lịch tiêm liên quan trước
        Lich.objects.filter(ma_vx=ma_vx).delete()
        
        # Sau đó xóa vaccine
        vacxin.delete()
        
        messages.success(request, "Xóa vắc xin và các lịch tiêm liên quan thành công!")
    
    return redirect("view_vacxin")

def view_khachhang(request):
    query = request.GET.get("q")
    if query:
        listKH = KhachHang.objects.filter(ho_ten__icontains=query)
    else:
        listKH = KhachHang.objects.all()
    return render(request, "view_khachhang.html", {"listKH": listKH, "query": query})


def delete_khachhang(request, ma_kh):
    khachhang = get_object_or_404(KhachHang, ma_kh=ma_kh)
    user = get_object_or_404(UserRole, MaKH=ma_kh)
    if request.method == "POST":
        # Xóa tất cả lịch liên quan đến khách hàng
        Lich.objects.filter(ma_kh=ma_kh).delete()
        #Xóa tài khoản
        user.delete()
        # Xóa khách hàng
        khachhang.delete()
        
        return redirect("view_khachhang")

    return redirect("view_khachhang")

def them_khach_hang(request):
    if request.method == "POST":
        ma_kh = generate_new_makh()
        ho_ten = request.POST.get("hotenkh").strip()
        so_dien_thoai = request.POST.get("sodienthoai").strip()
        dia_chi = request.POST.get("diachi").strip()
        ngay_sinh = request.POST.get("ngaysinh")
        gioi_tinh = request.POST.get("gioitinh")

        # Thêm khách hàng vào database
        KhachHang.objects.create(
            ma_kh=ma_kh,
            ho_ten=ho_ten,
            so_dien_thoai=so_dien_thoai,
            dia_chi=dia_chi,
            ngay_sinh=ngay_sinh,
            gioi_tinh=gioi_tinh
        )

        # Tạo tài khoản khách hàng với username & password là ma_kh, role = customer
        UserRole.objects.create(
            username=ma_kh,
            MaKH=ma_kh,
            password= ma_kh,  # Mã hóa mật khẩu
            role="customer"
        )
        # Thông báo và chuyển hướng
        return HttpResponse("""
            <script>
                alert("Thêm khách hàng thành công !");
                window.location.href = "/khachhang"; 
            </script>
        """)
    return render(request, "khachhang_them.html")

def cap_nhat_vacxin(request, mavacxin):
    vacxin = get_object_or_404(VacXin, MaVacXin=mavacxin)

    if request.method == "POST":
        vacxin.TenVacXin = request.POST["tenvacxin"]
        vacxin.SoMui = request.POST["somui"]
        vacxin.Mota = request.POST["mota"]
        vacxin.GiaVacXin = request.POST["giavacxin"]
        vacxin.TenHangSX = request.POST["tenhangvacxin"]

        hinh_anh_file = request.FILES.get("hinhanh")
        if hinh_anh_file:
            static_image_path = os.path.join(settings.BASE_DIR, 'myapp', 'static', 'images')
            os.makedirs(static_image_path, exist_ok=True)

            filename = hinh_anh_file.name
            save_path = os.path.join(static_image_path, filename)

            with open(save_path, 'wb+') as f:
                for chunk in hinh_anh_file.chunks():
                    f.write(chunk)

            relative_image_path = f"images/{filename}"
            vacxin.HinhAnh = relative_image_path  # Chỉ cập nhật nếu người dùng chọn file mới

        vacxin.save()
        return redirect("view_vacxin")

    return render(request, "cap_nhat_vacxin.html", {"vacxin": vacxin})

def xem_lich_su_tiem(request, ma_kh, ma_vx):
    list_lich = Lich.objects.filter(ma_kh=ma_kh, ma_vx=ma_vx).order_by("stt_mui")

    return render(request, "lich_su_tiem.html", {"list_lich": list_lich, "ma_kh": ma_kh})

def cap_nhat_lich(request):
    if request.method == "POST":
        ma_kh = request.POST.get('ma_kh')  # Lấy mã khách hàng từ form
        save_id = request.POST.get('save_id')  # Lấy id của lịch cần cập nhật

        try:
            lich = Lich.objects.get(id=save_id)
        except Lich.DoesNotExist:
            return redirect('xem_lich_admin')

        # Nếu mũi đã tiêm, không cho chỉnh sửa
        if lich.trangthai and request.POST.get(f"trangthai_{lich.id}") == "True":
            return redirect('lich_su_tiem', ma_kh=lich.ma_kh, ma_vx=lich.ma_vx)

        # Cập nhật ngày tiêm
        tg_tiem_str = request.POST.get(f"tg_tiem_{lich.id}")
        if tg_tiem_str:
            lich.tg_tiem = datetime.strptime(tg_tiem_str, '%Y-%m-%d').date()

        # Cập nhật trạng thái
        trangthai = request.POST.get(f"trangthai_{lich.id}")
        lich.trangthai = (trangthai == "True")

        lich.save()

        # Nếu có ngày tiêm mới thì cập nhật các mũi sau
        if tg_tiem_str:
            list_lich_sau = Lich.objects.filter(
                ma_kh=lich.ma_kh,
                ma_vx=lich.ma_vx,
                stt_mui__gt=lich.stt_mui
            ).order_by('stt_mui')

            for next_lich in list_lich_sau:
                khoang_cach = next_lich.stt_mui - lich.stt_mui
                next_lich.tg_tiem = lich.tg_tiem + timedelta(days=30 * khoang_cach)
                next_lich.save()

        return redirect('lich_su_tiem', ma_kh=lich.ma_kh.ma_kh, ma_vx=lich.ma_vx)

    return redirect('xem_lich_admin')

def danh_sach_yeu_cau(request):
    ds_yeu_cau = YeuCauDoiLich.objects.all().order_by('-ngay_gui')
    return render(request, 'duyet_yeu_cau.html', {'ds_yeu_cau': ds_yeu_cau})

def duyet_yeu_cau(request, id):
    yeu_cau = get_object_or_404(YeuCauDoiLich, id=id)

    if yeu_cau.trang_thai != 'cho_duyet':
        messages.warning(request, "Yêu cầu này đã được xử lý.")
        return redirect('danh_sach_yeu_cau')

    # Cập nhật lịch tiêm
    lich = yeu_cau.lich_cu
    lich.tg_tiem = yeu_cau.ngay_moi
    lich.save()

    # Cập nhật trạng thái yêu cầu
    yeu_cau.trang_thai = 'da_duyet'
    yeu_cau.save()

    messages.success(request, "Đã duyệt yêu cầu đổi lịch.")
    return redirect('danh_sach_yeu_cau')

def tu_choi_yeu_cau(request, id):
    yeu_cau = get_object_or_404(YeuCauDoiLich, id=id)
    yeu_cau.trang_thai = 'tu_choi'
    yeu_cau.save()
    messages.info(request, "Đã từ chối yêu cầu.")
    return redirect('danh_sach_yeu_cau')

def gui_yeu_cau_doi_lich(request, lich_id):
    lich = get_object_or_404(Lich, id=lich_id)

    # Kiểm tra quyền
    if request.session.get('role') != 'customer' or request.session.get('MaKH') != lich.ma_kh.ma_kh:
        messages.error(request, "Bạn không có quyền.")
        return redirect('lich_tiem_cua_toi')

    if request.method == 'POST':
        ngay_moi = parse_date(request.POST.get('ngay_moi'))
        ly_do = request.POST.get('ly_do')

        if ngay_moi and ly_do:
            YeuCauDoiLich.objects.create(
                lich_cu=lich,
                ngay_moi=ngay_moi,
                ly_do=ly_do,
            )
            return HttpResponse("<script>alert('Đã gửi yêu cầu thành công!'); window.history.back();</script>")
        else:
            messages.error(request, "Vui lòng nhập đầy đủ thông tin.")

    return render(request, 'gui_yeu_cau.html', {'lich': lich})

def xem_yeu_cau(request):
    user = request.session.get('username')
    role = request.session.get('role')

    if role != "customer":
        return redirect('login')

    # Kiểm tra đã đăng ký chưa
    MaKH = request.session['MaKH']
    danh_sach = YeuCauDoiLich.objects.filter(lich_cu__ma_kh=MaKH)
    return render(request, 'xem_yeu_cau.html', {'danh_sach': danh_sach})

def huy_yeu_cau(request, yc_id):
    user = request.session.get('username')
    role = request.session.get('role')

    if role != "customer":
        return redirect('login')

    # Kiểm tra đã đăng ký chưa
    MaKH = request.session['MaKH']

    yeu_cau = get_object_or_404(YeuCauDoiLich, id=yc_id, lich_cu__ma_kh=MaKH)

    if request.method == 'POST':
        yeu_cau.delete()
        return redirect('xem_yeu_cau')

    return redirect('xem_yeu_cau')