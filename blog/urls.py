"""
URL Configuration for blog app
"""
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # About page
    path('about/', views.about, name='about'),
    
    # Contact page
    path('contact/', views.contact, name='contact'),
    
    # Blog posts
    path('posts/', views.post_list, name='post_list'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    
    # Category pages
    path('category/<slug:category_slug>/', views.category_posts, name='category_posts'),
    
    # Search
    path('search/', views.search_posts, name='search'),
    
    # Archives by date
    path('archive/<int:year>/', views.year_archive, name='year_archive'),
    path('archive/<int:year>/<int:month>/', views.month_archive, name='month_archive'),
    
    # AJAX endpoints
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('subscribe/', views.newsletter_subscribe, name='subscribe'),
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('register/', views.register, name='register'),
]
