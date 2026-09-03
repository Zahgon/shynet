"""Form rendering helpers.

These are registered on the Jinja environment (see `shynet.templating`) and are
the direct equivalents of the `a17t` template filters: `a17t` renders a whole
form (or a single field) through the a17t partials, and the `is_*` predicates
tell the partial which widget to draw.
"""

from markupsafe import Markup
from wtforms import widgets
from wtforms.fields import Field, FieldList, FormField


def _render_template(name, **context):
    from flask import render_template

    return Markup(render_template(name, **context))


def a17t(element):
    markup_classes = {"label": "", "value": "", "single_value": ""}
    return render(element, markup_classes)


def a17t_inline(element):
    markup_classes = {"label": "", "value": "", "single_value": ""}
    return render(element, markup_classes)


def render(element, markup_classes):
    if isinstance(element, Field) and not isinstance(element, (FieldList, FormField)):
        return _render_template(
            "a17t/includes/field.html", field=element, classes=markup_classes
        )
    if isinstance(element, (FieldList, FormField)) or hasattr(
        element, "management_form"
    ):
        return _render_template(
            "a17t/includes/formset.html", formset=element, classes=markup_classes
        )
    return _render_template(
        "a17t/includes/form.html", form=element, classes=markup_classes
    )


def widget_type(field):
    return field.widget


def is_select(field):
    return isinstance(field.widget, widgets.Select)


def is_multiple_select(field):
    return isinstance(field.widget, widgets.Select) and field.widget.multiple


def is_textarea(field):
    return isinstance(field.widget, widgets.TextArea)


def is_input(field):
    return isinstance(
        field.widget,
        (
            widgets.TextInput,
            widgets.NumberInput,
            widgets.EmailInput,
            widgets.PasswordInput,
            widgets.URLInput,
            widgets.SearchInput,
            widgets.TelInput,
        ),
    ) and not isinstance(field.widget, widgets.HiddenInput)


def is_checkbox(field):
    return isinstance(field.widget, widgets.CheckboxInput)


def is_multiple_checkbox(field):
    return isinstance(field.widget, widgets.ListWidget) and _option_widget_is(
        field, widgets.CheckboxInput
    )


def is_radio(field):
    return isinstance(field.widget, widgets.ListWidget) and _option_widget_is(
        field, widgets.RadioInput
    )


def is_file(field):
    return isinstance(field.widget, widgets.FileInput)


def is_hidden(field):
    return isinstance(field.widget, widgets.HiddenInput)


def _option_widget_is(field, widget_class):
    option_widget = getattr(field, "option_widget", None)
    return isinstance(option_widget, widget_class)


def add_class(field, css_class):
    """Render `field` with `css_class` (plus the error class) applied."""
    if len(field.errors) > 0:
        css_class += " ~critical"
    existing = (field.render_kw or {}).get("class")
    if existing is not None:
        css_class += " " + existing
    kwargs = {k: v for k, v in (field.render_kw or {}).items() if k != "class"}
    return field(class_=css_class, **kwargs)


def hidden_fields(form):
    """The form's hidden fields, excluding the CSRF token (rendered separately)."""
    return [
        field
        for field in form
        if is_hidden(field) and field.name != "csrf_token"
    ]


def visible_fields(form):
    return [field for field in form if not is_hidden(field)]


def non_field_errors(form):
    return list(getattr(form, "form_errors", []) or [])
