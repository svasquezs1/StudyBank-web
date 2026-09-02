import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Q
from .forms import MaterialForm
from .models import Material, Course


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


def material_list(request):
    materials = Material.objects.select_related('course', 'university', 'uploaded_by').all()
    return render(request, 'materials/list.html', {'materials': materials})


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
    return render(request, 'materials/detail.html', {'material': material})


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

    materials = Material.objects.all()

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
    }
    return render(request, 'materials/list.html', context)