from django import template
from carousel.models import Slide

register = template.Library()

@register.inclusion_tag("carousel/carousel.html")
def show_carousel():
    return {"slides": list(Slide.objects.filter(active=True))}