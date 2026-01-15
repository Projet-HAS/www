
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from .models import Entreprise



# Formulaire de création d'un utilisateur
class UserCreateForm(forms.Form):
    User = get_user_model()
    # Identité
    first_name = forms.CharField(label=_("Prénom"), max_length=150, required=True)
    last_name = forms.CharField(label=_("Nom"), max_length=150, required=True)

    # Identifiant
    email = forms.EmailField(label=_("Email"), required=True)

    # Mot de passe
    password1 = forms.CharField(label=_("Mot de passe"), widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label=_("Confirmation du mot de passe"), widget=forms.PasswordInput, required=True)
    
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Un utilisateur avec cet email existe déjà.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("Les mots de passe ne correspondent pas."))
        # Valide selon les règles Django (force, longueur, etc.)
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error("password1", e)
        return cleaned

    def save(self):
        """
        Crée l'utilisateur et ajoute au groupe 'Administrator'
        Retourne l'instance User créée.
        """
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        first_name = self.cleaned_data["first_name"].strip()
        last_name = self.cleaned_data["last_name"].strip()

        user = User.objects.create_user(email=email, password=password)
        
        # Identité
        user.first_name = first_name
        user.last_name = last_name

        user.save()

        group, _ = Group.objects.get_or_create(name="Administrator")
        user.groups.add(group)

        return user


# Formulaire de création d'une entreprise
class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        # On exclut la PK et la date auto_now_add
        exclude = ["IDEntreprise", "Entreprise_Licence_Date_Start"]
        widgets = {
            "Entreprise_Licence_Date_End": forms.DateInput(attrs={"type": "date"}),
            # Tu peux ajouter des classes CSS si tu utilises Bootstrap/Tailwind
            "Entreprise_Name": forms.TextInput(attrs={"placeholder": "Nom de l'entreprise"}),
        }

    def clean(self):
        cleaned = super().clean()

        # Règles: created <= allow pour chaque couple
        couples = [
            ("Entreprise_Num_Customer_Create", "Entreprise_Num_Customer_Allow", "clients"),
            ("Entreprise_Num_User_Create", "Entreprise_Num_User_Allow", "utilisateurs"),
            ("Entreprise_Num_Supervisor_Create", "Entreprise_Num_Supervisor_Allow", "superviseurs"),
            ("Entreprise_Num_Group_Create", "Entreprise_Num_Group_Allow", "groupes"),
        ]

        for created_field, allow_field, label in couples:
            created = cleaned.get(created_field)
            allow = cleaned.get(allow_field)
            if created is not None and allow is not None and created > allow:
                self.add_error(
                    created_field,
                    f"Le nombre créé ({created}) ne peut pas dépasser le nombre autorisé ({allow}) pour les {label}."
                )

        # (Optionnel) Si statut ≠ ACTIVE, on peut exiger une date de fin
        statut = cleaned.get("Entreprise_Licence_Statut")
        date_fin = cleaned.get("Entreprise_Licence_Date_End")
        if statut in {"DIS", "ARC"} and not date_fin:
            self.add_error(
                "Entreprise_Licence_Date_End",
                "Veuillez renseigner une date de fin si la licence est désactivée ou archivée."
            )

        return cleaned
