from django.db import models

class UserRole(models.Model):
    username = models.CharField(max_length=255, primary_key=True) 
    MaKH = models.CharField(max_length=10)
    password = models.CharField(max_length=255) 
    role = models.CharField(max_length=100)

    class Meta:
        db_table = "userrole"  

    def __str__(self):
        return f"{self.username} - {self.role}"

class VacXin(models.Model):
    MaVacXin = models.CharField(max_length=50, primary_key=True)
    TenVacXin = models.CharField(max_length=100)
    SoMui = models.IntegerField()
    Mota = models.CharField(max_length=500)
    GiaVacXin = models.DecimalField(max_digits=10, decimal_places=2)
    TenHangSX = models.CharField(max_length=100)
    HinhAnh = models.CharField(max_length=255)

    class Meta:
        db_table = "VacXin"

    def __str__(self):
        return self.TenVacXin

class KhachHang(models.Model):
    ma_kh = models.CharField(max_length=10, primary_key=True, db_column="MaKH")
    ho_ten = models.CharField(max_length=100, db_column="HoTenKH")
    so_dien_thoai = models.CharField(max_length=10, db_column="SoDienThoai")
    dia_chi = models.TextField(db_column="DiachiKH")
    ngay_sinh = models.DateField(db_column="NgaySinh")
    gioi_tinh = models.CharField(max_length=10, db_column="GioiTinh")

    class Meta:
        db_table = 'customer'

class Lich(models.Model):
    id = models.AutoField(primary_key=True, db_column="id")  # Cột id tự động tăng
    ma_kh = models.ForeignKey(
        KhachHang,
        on_delete=models.CASCADE,
        db_column="MaKH",  
        to_field="ma_kh"   
    )
    ma_vx = models.CharField(max_length=50, db_column="MaVacXin")
    ten_vx = models.CharField(max_length=100, db_column="TenVacXin")
    stt_mui = models.IntegerField(db_column="STTMui")
    tg_tiem = models.DateField(db_column="TGTiem")
    trangthai = models.BooleanField(db_column="TrangThai")

    class Meta:
        db_table = 'history'

class YeuCauDoiLich(models.Model):
    id = models.AutoField(primary_key=True)
    lich_cu = models.ForeignKey(Lich, on_delete=models.CASCADE)
    ngay_moi = models.DateField()
    ly_do = models.TextField()
    trang_thai = models.CharField(
        max_length=20,
        choices=[('cho_duyet', 'Chờ duyệt'), ('da_duyet', 'Đã duyệt'), ('tu_choi', 'Từ chối')],
        default='cho_duyet'
    )
    ngay_gui = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'yeu_cau_doi_lich'

    def __str__(self):
        return f'Yêu cầu đổi lịch #{self.id} cho {self.lich_cu.ma_kh.ma_kh}'
