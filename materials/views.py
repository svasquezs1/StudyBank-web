import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Avg, Count, F, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce
from .forms import MaterialForm
from .models import Material, Course, MaterialDownload, MaterialRating
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

# RF-14: opciones de ordenamiento del catálogo (valor del parámetro ?sort=, etiqueta visible)
SORT_OPTIONS = [
    ('newest', 'Newest'),
    ('rating', 'Highest Rating'),
    ('downloads', 'Most Downloaded'),
]
DEFAULT_SORT = 'newest'


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
@never_cache
def download_material(request, pk):
    """
    Inicia la descarga directa del archivo con cabeceras Content-Disposition.
    Verifica que el archivo exista en disco/almacenamiento antes de servirlo.
    @never_cache evita que el navegador sirva descargas repetidas desde su caché:
    cada clic debe llegar al servidor para que se sume al total (RF-14).
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
            # RF-14: cada descarga repetida suma al total del material (incremento atómico en la base de datos)
            download.times_downloaded = F('times_downloaded') + 1
            download.save(update_fields=['times_downloaded', 'last_downloaded_at'])
        return response
    except Exception:
        messages.error(request, 'An error occurred while attempting to download the file.')
        return redirect('materials:detail', pk=pk)

@login_required
def search_materials(request):
    query = request.GET.get('q', '').strip()
    selected_course = request.GET.get('course', '').strip()

    # RF-14: criterio de ordenamiento (si el valor no es válido, se usa el predeterminado)
    sort_by = request.GET.get('sort', DEFAULT_SORT).strip()
    if sort_by not in dict(SORT_OPTIONS):
        sort_by = DEFAULT_SORT

    # 1. Obtenemos los nombres de las materias para listar en el select
    courses_list = Material.objects.values_list('course__name', flat=True).distinct().order_by('course__name')

    # RF-14: total de descargas del material (suma de todas las descargas de todos los usuarios).
    # Se calcula con una subconsulta para que no se multiplique al unirse con las calificaciones.
    total_downloads = (
        MaterialDownload.objects.filter(material=OuterRef('pk'))
        .values('material')
        .annotate(total=Sum('times_downloaded'))
        .values('total')
    )

    # RF-13 / RF-14: promedio, total de calificaciones y total de descargas en la misma consulta
    materials = Material.objects.annotate(
        avg_rating=Avg('ratings__score'),
        num_ratings=Count('ratings', distinct=True),
        download_total=Coalesce(Subquery(total_downloads), 0),
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

    # 4. Ordenamiento (RF-14). Siempre termina en -uploaded_at y -pk para que el orden sea determinista.
    if sort_by == 'rating':
        # Promedio de mayor a menor; sin calificaciones (promedio NULL) al final.
        # Desempate: más calificaciones primero, luego el más reciente.
        ordering = (F('avg_rating').desc(nulls_last=True), '-num_ratings', '-uploaded_at', '-pk')
    elif sort_by == 'downloads':
        ordering = ('-download_total', '-uploaded_at', '-pk')
    else:
        ordering = ('-uploaded_at', '-pk')

    materials = materials.distinct().order_by(*ordering)

    context = {
        'materials': materials,
        'courses_list': courses_list,
        'query': query,
        'selected_course': selected_course,
        'is_searched': bool(query or selected_course),
        'star_range': range(1, MaterialRating.MAX_SCORE + 1),
        'sort_by': sort_by,
        'sort_options': SORT_OPTIONS,
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

