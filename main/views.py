import random

from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache

from .models import Project, CrudtoberDay
from .lanyard_api import Lanyard


def index(request):
    page = {
        'title': 'Home',
        'description': "I'm Rayun. I make things.",
        'url': reverse('main:index')
    }
    greetings = ['Hello, world!', 'Greetings!', 'Hi there!', 'Yo!', 'Hey!', 'Hi!']
    return render(request, 'main/index.html', {
        'page': page,
        'greeting': random.choice(greetings)
    })


def projects(request):
    page = {
        'title': 'Projects',
        'description': "Projects I've worked on.",
        'url': reverse('main:projects')
    }
    projects = Project.objects.all().order_by('-date')
    return render(request, 'main/projects.html', {
        'page': page,
        'projects': projects
    })


def crudtober(request):
    page = {
        'title': 'Crudtober',
        'description': "A month-long challenge to do shit.",
        'url': reverse('main:crudtober')
    }
    crud = CrudtoberDay.objects.all().order_by('day')
    return render(request, 'main/crudtober.html', {
        'page': page,
        'crud': crud
    })


def reserved(request):
    return render(request, 'main/reserved.html')


@never_cache
async def lanyard(request):
    lan = Lanyard(344303001965428736)
    context = await lan.get_dict()
    return render(request, 'main/lanyard.html', context)
