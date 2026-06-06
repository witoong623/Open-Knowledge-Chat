---
name: backend-dev-guidelines
description: Guidelines for Django backend code and general python code. Use when working with Django python code, or explictly tell to check backend development guidelines.
---

# Backend Development Guidelines

## Model guideline
### Models should inherit TimeStampedModel based model
To get `created` and `modified` timestamps models should inherit from `TimeStampedModel` base model.
```python
from core.models import TimeStampedModel


class MyModel(TimeStampedModel):
    ...
```

### Setting model field blank and null argument
Use the following table to decide how to set `blank` and `null` argument of a model field.

| Field Type | Setting null=True | Setting blank=True |
|------------|-------------------|-------------------|
| CharField,<br>TextField,<br>SlugField,<br>EmailField,<br>CommaSeparated-<br>IntegerField,<br>UUIDField | Okay if you also have set both unique=True and blank=True. In this situation, null=True is required to avoid unique constraint violations when saving multiple objects with blank values. | Okay if you want the corresponding form widget to accept empty values. If you set this, empty values are stored as NULL in the database if null=True and unique=True are also set. Otherwise, they get stored as empty strings. |
| FileField,<br>ImageField | Don't do this. Django stores the path from MEDIA_ROOT to the file or to the image in a CharField, so the same pattern applies to FileFields. | Okay. The same pattern for CharField applies here. |
| BooleanField | Okay. | Default is blank=True. |
| IntegerField,<br>FloatField,<br>DecimalField,<br>DurationField, etc | Okay if you want to be able to set the value to NULL in the database. | Okay if you want the corresponding form widget to accept empty values. If so, you will also want to set null=True. |
| DateTimeField,<br>DateField,<br>TimeField, etc. | Okay if you want to be able to set the value to NULL in the database. | Okay if you want the corresponding form widget to accept empty values, or if you are using auto_now or auto_now_add. If it's the former, you will also want to set null=True. |
| ForeignKey,<br>OneToOneField | Okay if you want to be able to set the value to NULL in the database. | Okay if you want the corresponding form widget (e.g. the select box) to accept empty values. If so, you will also want to set null=True. |
| ManyToManyField | Null has no effect | Okay if you want the corresponding form widget (e.g. the select box) to accept empty values. |
| GenericIPAddressField | Okay if you want to be able to set the value to NULL in the database. | Okay if you want to make the corresponding field widget accept empty values. If so, you will also want to set null=True. |
| JSONField | Okay. | Okay. |

## Django development guidelines
### Use Django shell
If you want to check specific Django features by running code in Python interpreter. Please use Django shell to run to get better output.

## Django view guidelines
### Integrating HTMX with Django view
You can use [django-htmx](resources/django-htmx.md) package to help integrating HTMX with Django view e.g. check if request is made from HTMX or return response specifically for HTMX.
