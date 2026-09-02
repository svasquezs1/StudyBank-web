import os
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import MaterialForm
from .models import Material


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