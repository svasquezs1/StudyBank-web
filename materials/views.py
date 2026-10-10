import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from .forms import MaterialForm
from .models import Material, Course, MaterialDownload, MaterialRating
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count, Q


@login_required
def upload(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.uploaded_by = request.user
            material.save()
            messages.success(request, 'Study material uploaded successfully.')
            return redirect('materials:list')
    else:
        form = MaterialForm()

    return render(request, 'materials/upload.html', {'form': form})

@login_required
def material_list(request):
    """
    Entry point from the main menu ("Materials").
    Redirects to search_materials so the course filter (RF-06) is always populated
    with the list of available courses. @login_required enforces RNF-05.
    """
    return redirect('materials:search_materials')

@login_required
def material_detail(request, pk):
    """
    Muestra los detalles del material.
    Si el usuario no está autenticado, @login_required lo redirige automáticamente a /accounts/login/
    """
    material = get_object_or_404(
        Material.objects.select_related('course', 'university', 'uploaded_by'),
        pk=pk
    )
    summary = material.rating_summary()
    user_rating = material.rating_by(request.user)

    context = {
        'material': material,
        'average_rating': summary['average'],
        'rating_count': summary['count'],
        'has_downloaded': material.downloaded_by(request.user),
        'user_score': user_rating.score if user_rating else 0,
        'has_rated': user_rating is not None,
        'star_range': range(1, MaterialRating.MAX_SCORE + 1),
    }
    return render(request, 'materials/detail.html', context)


@login_required
def download_material(request, pk):
    """
    Inicia la descarga directa del archivo con cabeceras Content-Disposition.
    Verifica que el archivo exista en disco/almacenamiento antes de servirlo.
    """
    material = get_object_or_404(Material, pk=pk)

    # Si el archivo fue borrado o no existe en el storage
    if not material.file or not material.file.storage.exists(material.file.name):
        messages.error(request, 'The requested file no longer exists on the server.')
        return redirect('materials:detail', pk=pk)

    try:
        file_handle = material.file.open('rb')
        filename = os.path.basename(material.file.name)
        response = FileResponse(file_handle, as_attachment=True, filename=filename)
        # RF-13: registrar la descarga (una fila por usuario/material) para habilitar la calificación.
        download, created = MaterialDownload.objects.get_or_create(material=material, user=request.user)
        if not created:
            download.save(update_fields=['last_downloaded_at'])
        return response
    except Exception:
        messages.error(request, 'An error occurred while attempting to download the file.')
        return redirect('materials:detail', pk=pk)

@login_required
def search_materials(request):
    query = request.GET.get('q', '').strip()
    selected_course = request.GET.get('course', '').strip()

    # 1. Obtenemos los nombres de las materias para listar en el select
    courses_list = Material.objects.values_list('course__name', flat=True).distinct().order_by('course__name')

    # RF-13: promedio y total de calificaciones de cada material en la misma consulta
    materials = Material.objects.annotate(
        avg_rating=Avg('ratings__score'),
        num_ratings=Count('ratings', distinct=True),
    )

    # 2. Búsqueda por palabra clave (RF-05)
    if query:
        materials = materials.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(course__name__icontains=query)
        )

    # 3. Filtrado por Materia (RF-06)
    if selected_course:
        materials = materials.filter(course__name__iexact=selected_course)

    materials = materials.distinct().order_by('-uploaded_at')

    context = {
        'materials': materials,
        'courses_list': courses_list,
        'query': query,
        'selected_course': selected_course,
        'is_searched': bool(query or selected_course),
        'star_range': range(1, MaterialRating.MAX_SCORE + 1),
    }
    return render(request, 'materials/list.html', context)

@login_required
@require_POST
def rate_material(request, pk):
    """RF-13 — Califica un material de 1 a 5 estrellas (solo si lo descargó)."""
    material = get_object_or_404(Material, pk=pk)

    if not material.downloaded_by(request.user):
        messages.error(request, 'You need to download this material before you can rate it.')
        return redirect('materials:detail', pk=pk)

    try:
        score = int(request.POST.get('score', ''))
    except (TypeError, ValueError):
        score = None

    if score is None or score < MaterialRating.MIN_SCORE or score > MaterialRating.MAX_SCORE:
        messages.error(request, 'Please select a rating between 1 and 5 stars.')
        return redirect('materials:detail', pk=pk)

    # Una sola calificación por usuario/material: crea o actualiza (sin duplicar).
    MaterialRating.objects.update_or_create(
        material=material, user=request.user, defaults={'score': score}
    )
    messages.success(request, 'Thank you for rating this material!')
    return redirect('materials:detail', pk=pk)

