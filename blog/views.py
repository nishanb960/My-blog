"""
Views for blog app
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Sum  
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from datetime import timedelta
from .models import Post, Category, Comment
from .forms import ContactForm, CommentForm
import json
import calendar

def home(request):
    """Home page view"""
    featured_posts = Post.objects.filter(published=True, featured=True)[:3]
    recent_posts = Post.objects.filter(published=True).order_by('-created_at')[:5]
    categories = Category.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0)[:6]
    
    context = {
        'featured_posts': featured_posts,
        'recent_posts': recent_posts,
        'categories': categories,
        'title': 'Welcome to My Blog'
    }
    return render(request, 'blog/home.html', context)

def about(request):
    """About page view"""
    context = {
        'title': 'About Us',
        'description': 'Learn more about our blog and mission'
    }
    return render(request, 'blog/about.html', context)

def contact(request):
    """Contact page view"""
    form = ContactForm()
    context = {
        'title': 'Contact Us',
        'form': form
    }
    return render(request, 'blog/contact.html', context)

def post_list(request):
    """List all blog posts with pagination and filtering"""
    # Get query parameters
    layout = request.GET.get('layout', 'grid')
    sort = request.GET.get('sort', 'newest')
    category_filter = request.GET.getlist('category')
    date_filter = request.GET.get('date')
    
    # Base queryset
    posts = Post.objects.filter(published=True)
    
    # Apply category filter
    if category_filter:
        posts = posts.filter(categories__slug__in=category_filter).distinct()
    
    # Apply date filter
    if date_filter:
        if date_filter == 'week':
            posts = posts.filter(created_at__gte=timezone.now() - timedelta(days=7))
        elif date_filter == 'month':
            posts = posts.filter(created_at__gte=timezone.now() - timedelta(days=30))
        elif date_filter == 'year':
            posts = posts.filter(created_at__gte=timezone.now() - timedelta(days=365))
    
    # Apply sorting
    if sort == 'newest':
        posts = posts.order_by('-created_at')
    elif sort == 'oldest':
        posts = posts.order_by('created_at')
    elif sort == 'popular':
        posts = posts.order_by('-views', '-created_at')
    elif sort == 'commented':
        #  Count is already imported at the top
        posts = posts.annotate(comment_count=Count('comments')).order_by('-comment_count', '-created_at')
    elif sort == 'alphabetical':
        posts = posts.order_by('title')
    
    # Get featured post (most viewed in last 7 days)
    featured_post = Post.objects.filter(
        published=True,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-views', '-created_at').first()
    
    # Determine posts per page based on layout
    if layout == 'grid':
        per_page = 6
    elif layout == 'compact':
        per_page = 10
    else:  # list layout
        per_page = 5
    
    # Pagination
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for sidebar
    categories = Category.objects.annotate(
        post_count=Count('posts', filter=Q(posts__published=True))
    ).filter(post_count__gt=0).order_by('-post_count')
    
    # Get popular posts
    popular_posts = Post.objects.filter(published=True).order_by('-views', '-created_at')[:5]
    
    # Get statistics
    total_posts = Post.objects.filter(published=True).count()
    total_authors = User.objects.filter(posts__published=True).distinct().count()
    total_comments = Comment.objects.filter(approved=True).count()
    total_views = Post.objects.filter(published=True).aggregate(total=Sum('views'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'featured_post': featured_post,
        'categories': categories,
        'popular_posts': popular_posts,
        'total_posts': total_posts,
        'total_authors': total_authors,
        'total_comments': total_comments,
        'total_views': total_views,
        'title': 'Blog',
        'layout': layout,
        'sort': sort,
    }
    
    return render(request, 'blog/post_list.html', context)

def post_detail(request, post_id):
    """Display a single blog post"""
    post = get_object_or_404(Post, id=post_id, published=True)
    
    # Increment view count
    post.views += 1
    post.save(update_fields=['views'])
    
    # Get approved comments
    comments = post.comments.filter(approved=True)
    comment_form = CommentForm()
    
    # Get related posts (same categories)
    related_posts = Post.objects.filter(
        published=True,
        categories__in=post.categories.all()
    ).exclude(id=post.id).distinct().order_by('-created_at')[:3]
    
    # Get next and previous posts
    prev_post = Post.objects.filter(
        published=True, 
        created_at__lt=post.created_at
    ).order_by('-created_at').first()
    
    next_post = Post.objects.filter(
        published=True, 
        created_at__gt=post.created_at
    ).order_by('created_at').first()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'related_posts': related_posts,
        'prev_post': prev_post,
        'next_post': next_post,
        'title': post.title
    }
    return render(request, 'blog/post_detail.html', context)

def category_posts(request, category_slug):
    """Display posts by category"""
    category = get_object_or_404(Category, slug=category_slug)
    posts = category.posts.filter(published=True).order_by('-created_at')
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'title': f'Category: {category.name}'
    }
    return render(request, 'blog/category_posts.html', context)

def search_posts(request):
    """Search posts functionality"""
    query = request.GET.get('q', '')
    
    if query and len(query) >= 2:
        posts = Post.objects.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(excerpt__icontains=query),
            published=True
        ).distinct().order_by('-created_at')
    else:
        posts = Post.objects.none()
    
    context = {
        'posts': posts,
        'query': query,
        'title': f'Search results for "{query}"'
    }
    return render(request, 'blog/search_results.html', context)

def year_archive(request, year):
    """Display posts from a specific year"""
    posts = Post.objects.filter(
        created_at__year=year,
        published=True
    ).order_by('-created_at')
    
    context = {
        'posts': posts,
        'year': year,
        'title': f'Archive: {year}'
    }
    return render(request, 'blog/year_archive.html', context)

def month_archive(request, year, month):
    """Display posts from a specific month"""
    posts = Post.objects.filter(
        created_at__year=year,
        created_at__month=month,
        published=True
    ).order_by('-created_at')
    
    # Convert month number to name
    month_name = calendar.month_name[int(month)]
    
    context = {
        'posts': posts,
        'year': year,
        'month': month,
        'month_name': month_name,
        'title': f'Archive: {month_name} {year}'
    }
    return render(request, 'blog/month_archive.html', context)

@require_http_methods(["POST"])
def add_comment(request, post_id):
    """Add a comment to a post"""
    post = get_object_or_404(Post, id=post_id, published=True)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success', 'message': 'Comment added successfully! It will be visible after approval.'})
        else:
            messages.success(request, 'Your comment has been added! It will be visible after approval.')
            return redirect('blog:post_detail', post_id=post.id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")
        return redirect('blog:post_detail', post_id=post.id)

@require_http_methods(["POST"])
def newsletter_subscribe(request):
    """Handle newsletter subscription"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        # Here you would typically save to a NewsletterSubscriber model
        # or integrate with an email marketing service
        
        return JsonResponse({'status': 'success', 'message': 'Thank you for subscribing!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["POST"])
def contact_submit(request):
    """Handle contact form submission"""
    form = ContactForm(request.POST)
    
    if form.is_valid():
        # Here you would typically send an email or save to database
        return JsonResponse({'status': 'success', 'message': 'Thank you for your message! We\'ll get back to you soon.'})
    
    return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to MyBlog!')
            return redirect('blog:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# Error handlers
def custom_404(request, exception):
    return render(request, 'blog/404.html', status=404)

def custom_500(request):
    return render(request, 'blog/500.html', status=500)