from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import Usuario


# ==========================================================
#   Form creacion de usuario
# ==========================================================

class UsuarioCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Repetir contraseña",
        widget=forms.PasswordInput
    )

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol',
                  # Campos adicionales (opcionales)
                  'nombre', 'apellido', 'tipo_documento', 'documento',
                  'telefono', 'razon_social', 'cuit',
                  'calle', 'numero', 'localidad', 'provincia', 'pais'
                ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].help_text = "Ingrese un nombre de usuario único."

        # Campos exclusivos del rol transportista
        self.campos_transportista = [
            'telefono', 'razon_social', 'cuit',
            'calle', 'numero', 'localidad', 'provincia', 'pais'
        ]

        # Si el usuario NO es transportista, ocultar esos campos
        if self.instance and self.instance.rol != 'transportista':
            for campo in self.campos_transportista:
                self.fields.pop(campo, None)        

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        # Validar contraseñas
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden.")

        # Validación especial para transportistas
        if rol == 'transportista':
            campos_obligatorios = [
                'telefono', 'razon_social', 'cuit',
                'calle', 'numero', 'localidad', 'provincia', 'pais'
            ]
            for campo in campos_obligatorios:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Este campo es obligatorio para transportistas.")

        return cleaned_data

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.set_password(self.cleaned_data["password1"])

    #     if commit:
    #         user.save()
    #     return user
    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password1")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user



# ==========================================================
#   Form edicion usuario
# ==========================================================

class UsuarioUpdateForm(forms.ModelForm):
    password = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        required=False,
        help_text="Dejar vacía para mantener la contraseña actual."
    )


    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol',
                  'nombre', 'apellido', 'tipo_documento', 'documento',
                  'telefono', 'razon_social', 'cuit',
                  'calle', 'numero', 'localidad', 'provincia', 'pais']


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Campos exclusivos del rol transportista
        campos_transportista = [
            'telefono', 'razon_social', 'cuit',
            'calle', 'numero', 'localidad', 'provincia', 'pais'
        ]

        # Si el usuario NO es transportista, ocultar esos campos
        if self.instance and self.instance.rol != 'transportista':
            for campo in campos_transportista:
                self.fields.pop(campo, None)


    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get("rol")

        if rol == 'transportista':
            campos_obligatorios = [
                'telefono', 'razon_social', 'cuit',
                'calle', 'numero', 'localidad', 'provincia', 'pais'
            ]
            for campo in campos_obligatorios:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Este campo es obligatorio para transportistas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd = self.cleaned_data.get("password")
        if pwd:
            user.set_password(pwd)
        if commit:
            user.save()
        return user