from django.db import models

class Calon(models.Model):
    nama_calon = models.CharField(max_length=100)
    visi = models.TextField()
    misi = models.TextField()
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return self.nama_calon

class Pemilih(models.Model):
    nim = models.CharField(max_length=15, unique=True)
    nama = models.CharField(max_length=100)
    token = models.CharField(max_length=255, unique=True)
    sudah_memilih = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.nim} - {self.nama}"

class Vote(models.Model):
    PILIHAN_CHOICES = [
        ('calon', 'Memilih Calon'),
        ('abstain', 'Abstain'),
    ]
    
    pemilih = models.OneToOneField(Pemilih, on_delete=models.CASCADE)
    pilihan = models.CharField(max_length=10, choices=PILIHAN_CHOICES, db_index=True)
    calon = models.ForeignKey(Calon, on_delete=models.SET_NULL, null=True, blank=True)
    voted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.pemilih.nim} - {self.pilihan}"
