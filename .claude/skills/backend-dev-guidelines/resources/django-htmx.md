# django-htmx

## Overview

django-htmx is a Django package that provides extensions for using htmx with Django. It offers:

- Middleware to detect and handle htmx requests
- Template tags for including htmx scripts
- HTTP response helpers for htmx-specific behaviors
- Built-in CSRF token handling
- Vendored htmx library (version 2.0.7)

## Installation and Setup

### Basic Installation

```python
# Install the package
pip install django-htmx

# Add to INSTALLED_APPS in settings.py
INSTALLED_APPS = [
    # ...
    "django_htmx",
    # ...
]

# Add middleware
MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
    # ...
]
```

### Template Setup

In your base template, include the htmx script and CSRF configuration:

**Django Templates:**
```django
{% load django_htmx %}
<!doctype html>
<html>
<head>
    <!-- Other head content -->
    {% htmx_script %}
</head>
<body hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'>
    {% block content %}{% endblock %}
</body>
</html>
```

## Middleware and Request Detection

### HtmxMiddleware

The middleware adds `request.htmx` attribute to all requests, providing access to htmx-specific headers.

### HtmxDetails Attributes

Access htmx request information through `request.htmx`:

```python
from django.shortcuts import render

def my_view(request):
    # Check if request is from htmx
    if request.htmx:
        # Return partial template for htmx
        template_name = "partial.html"
    else:
        # Return full page template
        template_name = "complete.html"

    return render(request, template_name, context)
```

**Available attributes:**

- `request.htmx` - Boolean, True if request made with htmx (checks HX-Request header)
- `request.htmx.boosted` - Boolean, True if from hx-boost attribute (HX-Boosted header)
- `request.htmx.current_url` - Current browser URL (HX-Current-URL header)
- `request.htmx.current_url_abs_path` - Absolute path of current URL (without scheme/netloc)
- `request.htmx.history_restore_request` - Boolean, True if history restoration request (HX-History-Restore-Request header)
- `request.htmx.prompt` - User response to hx-prompt, or None (HX-Prompt header)
- `request.htmx.target` - ID of target element, or None (HX-Target header)
- `request.htmx.trigger` - ID of triggered element, or None (HX-Trigger header)
- `request.htmx.trigger_name` - Name of triggered element, or None (HX-Trigger-Name header)
- `request.htmx.triggering_event` - Deserialized JSON event that triggered request, or None (requires event-header htmx extension)

### Type Hinting

For type-checking with django-stubs:

```python
from django.http import HttpRequest as HttpRequestBase
from django_htmx.middleware import HtmxDetails

class HttpRequest(HttpRequestBase):
    htmx: HtmxDetails
```

### Caching Considerations

When using HTTP caching with htmx-aware views, add appropriate Vary headers:

```python
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.vary import vary_on_headers

@cache_control(max_age=300)
@vary_on_headers("HX-Request")
def my_view(request):
    if request.htmx:
        template_name = "partial.html"
    else:
        template_name = "complete.html"
    return render(request, template_name, context)
```

## HTTP Response Helpers

### HttpResponseClientRedirect

Client-side redirect using HX-Redirect header:

```python
from django_htmx.http import HttpResponseClientRedirect

def sensitive_view(request):
    if not user_authenticated(request):
        return HttpResponseClientRedirect("/login/")
    # ... rest of view
```

### HttpResponseClientRefresh

Trigger full page reload using HX-Refresh header:

```python
from django_htmx.http import HttpResponseClientRefresh

def partial_table_view(request):
    if data_outdated(request):
        return HttpResponseClientRefresh()
    # ... rest of view
```

### HttpResponseLocation

Advanced client-side redirect with options using HX-Location header:

```python
from django_htmx.http import HttpResponseLocation

def wait_for_completion(request, action_id):
    action = get_object_or_404(Action, id=action_id)
    if action.completed:
        return HttpResponseLocation(
            f"/action/{action.id}/completed/",
            source="#action-status",
            target="#main-content",
            swap="innerHTML"
        )
    # ... rest of view
```

**Parameters:**
- `redirect_to` - URL to redirect to
- `source` - Source element of request (optional)
- `event` - Event that triggered request (optional)
- `target` - Target element for swap (optional)
- `swap` - Swap method (optional)
- `select` - CSS selector for content (optional)
- `values` - Values to submit with request (optional)
- `headers` - Additional headers (optional)

### HttpResponseStopPolling

Stop htmx polling with status code 286:

```python
from django_htmx.http import HttpResponseStopPolling

def my_pollable_view(request):
    if event_finished():
        return HttpResponseStopPolling()
    # ... continue polling
```

Or use the constant with render:

```python
from django.shortcuts import render
from django_htmx.http import HTMX_STOP_POLLING

def my_pollable_view(request):
    if event_finished():
        return render(request, "finished.html", status=HTMX_STOP_POLLING)
```

### Header Manipulation Functions

**push_url** - Update browser history:

```python
from django_htmx.http import push_url

def leaf_view(request, leaf_id):
    leaf = get_object_or_404(Leaf, id=leaf_id)
    if leaf is None:
        response = branch_view(request, branch=leaf.branch)
        return push_url(response, f"/branch/{leaf.branch.id}/")
    # ... rest of view
```

**replace_url** - Replace current URL in history:

```python
from django_htmx.http import replace_url

def search_view(request):
    results = search(request.GET.get('q'))
    response = render(request, "results.html", {'results': results})
    return replace_url(response, f"/search/?q={request.GET.get('q')}")
```

**trigger_client_event** - Trigger client-side events:

```python
from django_htmx.http import trigger_client_event

def my_view(request):
    response = render(request, "template.html", context)
    trigger_client_event(
        response,
        "showMessage",
        {"message": "Operation completed", "level": "success"},
        after="receive"  # or "settle" or "swap"
    )
    return response
```

**Parameters for trigger_client_event:**
- `after="receive"` - Fire event after receiving response (default)
- `after="settle"` - Fire event after DOM settling
- `after="swap"` - Fire event after content swap

## Common Patterns

### Partial Template Rendering

**Pattern 1: Conditional template selection**

```python
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

def my_view(request: HttpRequest) -> HttpResponse:
    context = get_context_data()

    if request.htmx:
        # Return only the partial for htmx requests
        template = "partials/content.html"
    else:
        # Return full page for regular requests
        template = "full_page.html"

    return render(request, template, context)
```

**Pattern 2: Using template inheritance with base template swapping**

```python
def my_view(request):
    if request.htmx:
        base_template = "_partial.html"
    else:
        base_template = "_base.html"

    return render(request, "page.html", {
        "base_template": base_template,
        # ... other context
    })
```

Template:
```django
{% extends base_template %}
{% block content %}
    <!-- Your content here -->
{% endblock %}
```

**Pattern 3: Using template partials**

Template:
```django
{% extends "_base.html" %}

{% block main %}
    <h1>Countries</h1>

    {% partialdef country-table inline %}
    <table id="country-data">
        <thead>...</thead>
        <tbody>
            {% for country in countries %}
                <tr>...</tr>
            {% endfor %}
        </tbody>
    </table>
    {% endpartialdef %}
{% endblock main %}
```

View:
```python
from django.shortcuts import render

def countries_view(request):
    countries = Country.objects.all()
    context = {"countries": countries}

    if request.htmx:
        return render(
            request,
            "countries.html#country-table",
            context
        )

    return render(request, "countries.html", context)
```

### Form Validation

Handle inline form validation with htmx:

```python
from django.shortcuts import render
from django.views.decorators.http import require_POST

@require_POST
def validate_field(request):
    form = MyForm(request.POST)

    if form.is_valid():
        # Return success indicator
        return render(request, "partials/field_valid.html")
    else:
        # Return error messages
        return render(request, "partials/field_errors.html", {
            "errors": form.errors
        })
```

### Infinite Scroll

```python
from django.core.paginator import Paginator

def infinite_scroll_view(request):
    page_number = request.GET.get('page', 1)
    items = MyModel.objects.all()
    paginator = Paginator(items, 10)
    page = paginator.get_page(page_number)

    if request.htmx:
        template = "partials/items_list.html"
    else:
        template = "items_page.html"

    return render(request, template, {
        "items": page.object_list,
        "page": page,
    })
```

Template:
```django
<div id="items-container">
    {% for item in items %}
        <div class="item">{{ item.name }}</div>
    {% endfor %}
</div>

{% if page.has_next %}
<div hx-get="?page={{ page.next_page_number }}"
     hx-trigger="revealed"
     hx-swap="afterend">
    Loading...
</div>
{% endif %}
```

### CSRF Protection

The recommended approach is to add the CSRF token globally via hx-headers on the body tag:

```django
<body hx-headers='{"x-csrftoken": "{{ csrf_token }}"}'>
```

This makes all htmx requests within the body include the CSRF token.

**Alternative: JavaScript event listener**

```javascript
document.body.addEventListener('htmx:configRequest', (event) => {
    event.detail.headers['X-CSRFToken'] = '{{ csrf_token }}';
});
```

**Note:** Use `{{ csrf_token }}` (the variable), not `{% csrf_token %}` (the tag that renders an input).

## Best Practices

1. **Always use the middleware** - It provides clean access to htmx request information
2. **Set Vary headers** - When caching htmx-aware views, use `@vary_on_headers("HX-Request")`
3. **Keep partials focused** - Partial templates should be self-contained and reusable
4. **Use django-htmx HTTP helpers** - They handle htmx headers correctly
5. **Test both paths** - Ensure views work for both htmx and non-htmx requests
6. **CSRF protection** - Always configure CSRF tokens for POST/PUT/PATCH/DELETE requests
7. **Use template partials** - Consider django-template-partials for complex partial rendering
8. **Debug mode benefits** - The debug error handler is invaluable during development

## Common Gotchas

1. **Missing CSRF token** - Results in 403 errors on unsafe methods (POST, PUT, DELETE)
2. **Not varying on HX-Request** - Causes incorrect cached responses when mixing htmx and non-htmx requests
3. **Forgetting middleware** - `request.htmx` won't be available without HtmxMiddleware
4. **Over-rendering** - Returning full page when partial would suffice wastes bandwidth
5. **Not handling both request types** - Views should gracefully handle both htmx and regular requests

## Additional Resources

- Official docs: https://django-htmx.readthedocs.io/
- htmx docs: https://htmx.org/
- Example project included in django-htmx package demonstrates all features
