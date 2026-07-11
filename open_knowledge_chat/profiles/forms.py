from django import forms

from chat.llm.registry import MODELS, tool_choices
from profiles.models import ChatProfile


class ChatProfileForm(forms.ModelForm):
    # enabled_tools is a JSONField (list of keys) on the model; expose it as
    # checkboxes whose values are validated against the tool registry.
    enabled_tools = forms.MultipleChoiceField(
        choices=tool_choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Available tools',
    )

    class Meta:
        model = ChatProfile
        fields = ['name', 'model_key', 'temperature', 'use_reasoning', 'system_prompt', 'enabled_tools']
        widgets = {
            'system_prompt': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        spec = MODELS.get(cleaned.get('model_key'))
        if spec is not None:
            if cleaned.get('temperature') is not None and not spec.supports_temperature:
                self.add_error('temperature', f'{spec.label} does not support a temperature setting.')
            if cleaned.get('use_reasoning') and not spec.supports_reasoning:
                self.add_error('use_reasoning', f'{spec.label} does not support reasoning.')
        return cleaned
