import random

from django.shortcuts import render
from django.urls import reverse

from .models import Project


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


def reserved(request):
    return render(request, 'main/reserved.html')
