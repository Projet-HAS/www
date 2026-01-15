from django.contrib import admin
from .models import Entreprise, Compte
from django.contrib.auth.admin import UserAdmin

from django import forms
from django.utils.translation import gettext_lazy as _


# Register your models here.

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ("IDEntreprise", "Entreprise_Name", "Entreprise_Licence_Statut",
                    "Entreprise_Licence_Date_Start", "Entreprise_Licence_Date_End")
    search_fields = ("Entreprise_Name",)
    list_filter = ("Entreprise_Licence_Statut",)


class CompteCreationForm(forms.ModelForm):
    """Formulaire de création (admin) avec double mot de passe."""
    password1 = forms.CharField(label=_("Mot de passe"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirmation"), widget=forms.PasswordInput)

    class Meta:
        model = Compte
        fields = ("username", "email", "first_name", "last_name",
                  "Compte_IDEntreprise", "Compte_Image")

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_("Les mots de passe ne correspondent pas."))
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class CompteChangeForm(forms.ModelForm):
    """Formulaire de modification (admin). Le mot de passe est géré par UserAdmin."""
    class Meta:
        model = Compte
        fields = ("username", "email", "first_name", "last_name",
                  "is_active", "is_staff", "is_superuser",
                  "Compte_IDEntreprise", "Compte_Image", "groups", "user_permissions")

@admin.register(Compte)
class CompteAdmin(UserAdmin):
    add_form = CompteCreationForm
    form = CompteChangeForm
    model = Compte

    # Ce qui s’affiche dans la liste admin
    list_display = ("username", "email", "Compte_IDEntreprise", "is_staff", "is_active")
    list_filter = ("is_staff", "is_active", "Compte_IDEntreprise", "groups")

    # Groupes de champs (édition)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Informations personnelles"), {
            "fields": ("first_name", "last_name", "email", "Compte_Image", "Compte_IDEntreprise")
        }),
        (_("Permissions"), {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")
        }),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )

    # Groupes de champs (création)
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "email", "first_name", "last_name",
                "Compte_IDEntreprise", "Compte_Image",
                "password1", "password2",
                "is_staff", "is_active"
            ),
        }),
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
