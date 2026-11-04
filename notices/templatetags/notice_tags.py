from django import template
from notices.models import Banner

register = template.Library()

@register.inclusion_tag("notices/banner.html")
def show_banner():
    return {"banners": list(Banner.objects.filter(active=True))}