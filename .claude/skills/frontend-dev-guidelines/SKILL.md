---
name: frontend-dev-guidelines
description: Frontend development guidelines for Django applications. Frontend including Django template, HTMX and Alpine.js. Use when implementing frontend or working with frontend code, or explicitly tell to check frontend development guidelines.
---

# Frontend Development Guideline

## Django template guideline
### Using partial tags

Use `{% partialdef %}` to define partial template in any template file.
Use `{% partial %}` to render partial in template file.

For example in `cluster/index.html` file.
```html
{% partialdef name-of-partial %}
<h1>This is HTML in partial definition</h1>
{% endpartialdef %}

<!-- other HTML/Django template contents -->

<!-- render partial template here -->
{% partial name-of-partial %}
```

You can also use `inline` modifier to render the partial at the definition location AND make it available for later use:
```html
{% partialdef greeting-partial inline %}
<h1>Hello, this renders immediately!</h1>
{% endpartialdef %}

<!-- The greeting is already rendered above, but can also be reused -->
{% partial greeting-partial %}
```

In Python code, if you use partial definition syntax above, you can refer to partial definition using `template_name#partial_name` in `get_template()`, `render()` or in Django template `{% include %}`.
This will return rendered content inside partial.
```python
def index(request):
    return render(request, 'cluster/index.html#name-of-partial')
```

If you define separate template file, and use `{% include %}` to include it in another template, or to return rendered HTML from view function, this isn't "partial template" that I showed here.
This is just a template usage. You must refer to that template using full template name i.e. `cluster/partials/some-fragment.html`.

## HTMX guideline
See HTMX reference in [HTML Reference](resources/htmx-reference.md).
