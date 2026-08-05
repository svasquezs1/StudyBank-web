from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
