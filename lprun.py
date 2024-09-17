import uuid
import inspect
from django.test import RequestFactory
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth.models import User
from line_profiler import LineProfiler
    

def lprun(fn_to_run, *args, fn_to_monitor=None, **kwargs):
    if fn_to_monitor is None:
        fn_to_monitor = fn_to_run

    # Create a unique user
    unique_username = f'user_{uuid.uuid4().hex[:8]}'
    user = User.objects.create_user(username=unique_username, password='temporary_password')
    
    try:
        sig = inspect.signature(fn_to_run)
        first_param = next(iter(sig.parameters.values()))
        if first_param.name == 'request':
            # Authenticate the user
            authenticated_user = authenticate(username=unique_username, password='temporary_password')
            
            # Create a request object
            request = RequestFactory().get('/dummy/')
            request.user = authenticated_user # type: ignore #
            
            # Prepare the arguments
            args = (request, *args)
        
        # Access the original function
        fn_to_monitor = fn_to_monitor.__wrapped__ if hasattr(fn_to_monitor, '__wrapped__') else fn_to_monitor
        lp = LineProfiler()
        lp.add_function(fn_to_monitor)
        lp.enable_by_count()
        result = fn_to_run(*args, **kwargs)
        lp.disable_by_count()
        lp.print_stats()
    finally:
        # Delete the user after the function execution
        user.delete()