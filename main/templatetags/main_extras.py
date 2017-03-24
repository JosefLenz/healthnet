from django import template

register = template.Library()


def usercheck(value, arg):
    """Checks if user is a of a certain type in a template"""
    if hasattr(value, arg):
        return True
    else:
        return False

register.filter('usercheck', usercheck)
