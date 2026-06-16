def user_context(request):
    return {'user_role': getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'}
