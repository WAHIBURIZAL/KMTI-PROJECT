from datetime import datetime, timedelta, timezone as dt_timezone

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.utils import timezone
from .models import Calon, Pemilih, Vote
from django.http import JsonResponse

WIB = dt_timezone(timedelta(hours=7), 'WIB')
VOTING_CLOSE_AT = datetime(2026, 5, 4, 16, 0, tzinfo=WIB)


def is_voting_closed():
    return timezone.now() >= VOTING_CLOSE_AT


# ==================== SATU LOGIN UNTUK SEMUA ====================

def login_view(request):
    """Satu halaman login untuk voter dan admin"""
    if request.method == 'POST':
        nim = request.POST.get('nim', '').strip()
        token = request.POST.get('token', '').strip()
        
        if not nim or not token:
            messages.error(request, 'NIM dan token harus diisi!')
            return render(request, 'pemilwa/login.html')
        
        try:
            pemilih = Pemilih.objects.only('id', 'nim', 'nama', 'sudah_memilih').get(nim=nim, token=token)

            is_admin = str(pemilih.nim).startswith("67")
            
            if is_admin:
                # Login sebagai admin
                request.session['is_admin'] = True
                request.session['admin_nim'] = pemilih.nim
                request.session['admin_nama'] = pemilih.nama
                messages.success(request, f'Selamat datang {pemilih.nama}!')
                return redirect('pemilwa:admin_dashboard')
            else:
                # Login sebagai voter biasa
                if pemilih.sudah_memilih and not is_voting_closed():
                    messages.error(request, 'Anda sudah melakukan pemilihan!')
                else:
                    request.session['pemilih_id'] = pemilih.id
                    request.session['pemilih_nim'] = pemilih.nim
                    request.session['pemilih_nama'] = pemilih.nama
                    return redirect('pemilwa:voting_page')
                    
        except Pemilih.DoesNotExist:
            messages.error(request, 'NIM atau token salah!')
    
    return render(request, 'pemilwa/login.html')


# ==================== VOTER SIDE ====================

def voting_page(request):
    """Halaman voting untuk voter"""
    if not request.session.get('pemilih_id'):
        return redirect('pemilwa:login')
    
    pemilih_id = request.session.get('pemilih_id')
    
    try:
        pemilih = Pemilih.objects.only('id', 'nim', 'nama', 'sudah_memilih').get(id=pemilih_id)
        voting_closed = is_voting_closed()

        if voting_closed:
            context = {
                'nim': pemilih.nim,
                'nama': pemilih.nama,
                'voting_closed': True,
            }
            return render(request, 'pemilwa/voting.html', context)
        
        if pemilih.sudah_memilih:
            return redirect('pemilwa:thanks')
        
        calon_aktif = Calon.objects.only('nama_calon', 'visi', 'misi').filter(is_active=True).first()
        
        if not calon_aktif:
            messages.error(request, 'Belum ada calon yang terdaftar!')
            return redirect('pemilwa:login')
        
        context = {
            'calon': calon_aktif,
            'nim': pemilih.nim,
            'nama': pemilih.nama,
            'voting_closed': False,
        }
        return render(request, 'pemilwa/voting.html', context)
    
    except Pemilih.DoesNotExist:
        if 'pemilih_id' in request.session:
            del request.session['pemilih_id']
        return redirect('pemilwa:login')


def submit_vote(request):
    """Proses submit vote (calon atau abstain)"""
    if request.method != 'POST':
        return redirect('pemilwa:voting_page')
    
    pemilih_id = request.session.get('pemilih_id')
    if not pemilih_id:
        return redirect('pemilwa:login')
    
    try:
        if is_voting_closed():
            messages.error(request, 'Pemungutan suara sudah ditutup.')
            return redirect('pemilwa:voting_page')

        pilihan = request.POST.get('pilihan')

        with transaction.atomic():
            pemilih = Pemilih.objects.select_for_update().only('id', 'sudah_memilih').get(id=pemilih_id)

            if pemilih.sudah_memilih:
                return redirect('pemilwa:thanks')

            if pilihan == 'calon':
                calon_aktif = Calon.objects.only('id').filter(is_active=True).first()
                if not calon_aktif:
                    messages.error(request, 'Calon tidak tersedia!')
                    return redirect('pemilwa:voting_page')

                Vote.objects.create(
                    pemilih=pemilih,
                    pilihan='calon',
                    calon=calon_aktif
                )

            elif pilihan == 'abstain':
                Vote.objects.create(
                    pemilih=pemilih,
                    pilihan='abstain',
                    calon=None
                )
            else:
                messages.error(request, 'Pilihan tidak valid!')
                return redirect('pemilwa:voting_page')

            pemilih.sudah_memilih = True
            pemilih.save(update_fields=['sudah_memilih'])
        
        for key in ('pemilih_id', 'pemilih_nim', 'pemilih_nama'):
            request.session.pop(key, None)
        
        return redirect('pemilwa:thanks')
        
    except Pemilih.DoesNotExist:
        return redirect('pemilwa:login')
    except IntegrityError:
        return redirect('pemilwa:thanks')
    except Exception as e:
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('pemilwa:voting_page')


def thanks_view(request):
    """Halaman terima kasih setelah voting"""
    return render(request, 'pemilwa/thanks.html')


def voter_logout(request):
    """Logout voter (hapus session voter)"""
    for key in ('pemilih_id', 'pemilih_nim', 'pemilih_nama'):
        request.session.pop(key, None)
    messages.info(request, 'Anda telah logout.')
    return redirect('pemilwa:login')


# ==================== ADMIN SIDE ====================

def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('pemilwa:login')

    calon_aktif = Calon.objects.only('nama_calon').filter(is_active=True).first()

    vote_stats = Vote.objects.aggregate(
        suara_calon=Count('id', filter=Q(pilihan='calon')),
        suara_abstain=Count('id', filter=Q(pilihan='abstain')),
    )
    suara_calon = vote_stats['suara_calon']
    suara_abstain = vote_stats['suara_abstain']
    total_suara_masuk = suara_calon + suara_abstain

    total_db = Pemilih.objects.count()
    total_voter_riil = total_db - 1 if total_db > 0 else 0

    persen_calon = (suara_calon / total_suara_masuk * 100) if total_suara_masuk else 0
    persen_abstain = (suara_abstain / total_suara_masuk * 100) if total_suara_masuk else 0

    chart_data = {
        'labels': [calon_aktif.nama_calon if calon_aktif else 'Calon', 'Abstain'],
        'data': [suara_calon, suara_abstain],
        'colors': ['#DED479', '#BEC4D9'],
        'total_vote': total_suara_masuk
    }

    # Jika fetch AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(chart_data)

    context = {
        'calon': calon_aktif,
        'suara_calon': suara_calon,
        'suara_abstain': suara_abstain,
        'total_pemilih': total_suara_masuk,
        'total_terdaftar': total_voter_riil,
        'belum_memilih': max(total_voter_riil - total_suara_masuk, 0),
        'persen_calon': round(persen_calon, 1),
        'persen_abstain': round(persen_abstain, 1),
        'chart_data': chart_data,
    }

    return render(request, 'pemilwa/admin_dashboard.html', context)


def admin_logout(request):
    """Logout admin (hapus session admin)"""
    for key in ('is_admin', 'admin_nim', 'admin_nama'):
        request.session.pop(key, None)
    messages.info(request, 'Admin telah logout.')
    return redirect('pemilwa:login')
