from django import template
from django.utils import timezone
from django.db.models import Count  # Add this import
from blog.models import Category, Post
import math

register = template.Library()

@register.simple_tag
def get_categories():
    """Get all categories with post counts"""
    return Category.objects.annotate(post_count=Count('posts')).filter(post_count__gt=0)

@register.simple_tag
def get_popular_posts(limit=5):
    """Get most viewed posts"""
    return Post.objects.filter(published=True).order_by('-views')[:limit]

@register.filter
def read_time(content):
    """Calculate estimated reading time"""
    if not content:
        return 1
    words = len(content.split())
    minutes = math.ceil(words / 200)  # Average reading speed: 200 words per minute
    return max(1, minutes)  # At least 1 minute

@register.filter
def time_until(date):
    """Return time until given date"""
    if not date:
        return ""
    
    now = timezone.now()
    diff = date - now
    
    if diff.days > 0:
        return f"{diff.days} days from now"
    elif diff.days == 0:
        hours = diff.seconds // 3600
        if hours > 0:
            return f"{hours} hours from now"
        minutes = (diff.seconds % 3600) // 60
        if minutes > 0:
            return f"{minutes} minutes from now"
        return "soon"
    return ""

@register.simple_tag(takes_context=True)
def url_replace(context, field, value):
    """Replace a field's value in the URL query string"""
    request = context['request']
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()