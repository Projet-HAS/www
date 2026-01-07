from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, F, CheckConstraint
from django.db.models.functions import Length
from django.db.models.expressions import RawSQL
from django.contrib.auth.models import User, Group, AbstractUser, BaseUserManager

#Pour la création des groupes d'utilisateurs
from django.db.models.signals import post_migrate
from django.dispatch import receiver



####################################
# Liste des groupes d'utilisateurs #
####################################
DEFAULT_GROUPS = [
    "Administrator",
    "Supervisor",
    "Customer",
    "SKT_User",    
]

####################################################################
# Modification du user pour qu'il prenne l'email comme identifiant #
####################################################################
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("L'email est requis")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superuser doit avoir is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    # On supprime l'unicité du username en pratique en le rendant optionnel
    username = models.CharField(max_length=150, blank=True, null=True, unique=False)
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"          # email devient l’identifiant
    REQUIRED_FIELDS = []              # pas de champs requis en plus pour createsuperuser

    objects = UserManager()

    def __str__(self):
        return self.email


########################
# Table des Entreprise #
########################
class Entreprise(models.Model) :
    #IDEntreprise est une clè primaire auto-incrémentée
    IDEntreprise = models.AutoField(primary_key = True)

    #Nom de l'entreprise (chaîne de caractère)
    Entreprise_Name = models.CharField(max_length = 255)

    #Date de début de la licence (affectation automatique avec la date du jour)
    Entreprise_Licence_Date_Start = models.DateField(auto_now_add=True)

    #Date de findébut de la licence (possible de laisser vide)
    Entreprise_Licence_Date_End = models.DateField(null=True, blank=True)

    #Statut de la licence entreprise
    class LicenceStatut(models.TextChoices):
        ACTIVE = 'ACT', 'Active'
        DISABLED = 'DIS', 'Disable'
        ARCHIVED = 'ARC', 'Archive'

    # Statut avec Enum + choices
    Entreprise_Licence_Statut = models.CharField(
        max_length=3,  
        choices=LicenceStatut.choices,
        default=LicenceStatut.ACTIVE,
    )

    #Nombre de compte clients autorisés (entre 0 et 999)
    Entreprise_Num_Customer_Allow = models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("Le nombre de clients autorisés peut pas être négative (min = 0).")),
            MaxValueValidator(999, message=_("Le nombre de clients autorisés ne peut pas dépasser  999.")),
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Le nombre de clients autorisés est requis."),
        },
        help_text=_("Entier compris entre 0 et 99 999.")
    )

    #Nombre de compte clients créés (entre 0 et le nombre de client autorisés)
    Entreprise_Num_Customer_Create =  models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("La valeur ne peut pas être négative."))
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Ce champ est requis."),
        },
        help_text=_("Entier ≥ 0 et ≤ au nombre de clients autorisées ")
    )

    #Nombre de compte utilisateurs autorisés (entre 0 et 99 999)
    Entreprise_Num_User_Allow = models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("Le nombre d'utilisateurs ne peut pas être négative (min = 0).")),
            MaxValueValidator(99999, message=_("Le nombre d'utilisateurs ne peut pas dépasser 99 999.")),
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Le nombre d'utilisateurs autorisés est requis."),
        },
        help_text=_("Entier compris entre 0 et 99 999.")
    )

    #Nombre de compte utilisateurs créés (entre 0 et le nombre d'utilisateurs autorisés)
    Entreprise_Num_User_Create =  models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("La valeur ne peut pas être négative."))
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Ce champ est requis."),
        },
        help_text=_("Entier ≥ 0 et ≤ au nombre d'utilisateurs autorisés ")
    )

    #Nombre de compte superviseur autorisés (entre 0 et 9 999)
    Entreprise_Num_Supervisor_Allow = models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("Le nombre de superviseur ne peut pas être négative (min = 0).")),
            MaxValueValidator(9999, message=_("Le nombre de superviseur ne peut pas dépasser 9 999.")),
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Le nombre de superviseurs autorisés est requis."),
        },
        help_text=_("Entier compris entre 0 et 9 999.")
    )

    #Nombre de compte superviseur créés (entre 0 et le nombre d'utilisateurs autorisés)
    Entreprise_Num_Supervisor_Create =  models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("La valeur ne peut pas être négative."))
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Ce champ est requis."),
        },
        help_text=_("Entier ≥ 0 et ≤ au nombre de superviseurs autorisés ")
    )

    #Nombre de groupes autorisés (entre 0 et 9 999)
    Entreprise_Num_Group_Allow = models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("Le nombre de groupe ne peut pas être négative (min = 0).")),
            MaxValueValidator(9999, message=_("Le nombre de groupe ne peut pas dépasser 9 999.")),
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Le nombre de groupe autorisés est requis."),
        },
        help_text=_("Entier compris entre 0 et 9 999.")
    )

    #Nombre de groupes créés (entre 0 et le nombre de groupes autorisés)
    Entreprise_Num_Group_Create =  models.IntegerField(       
        default=0,
        validators=[
            MinValueValidator(0, message=_("La valeur ne peut pas être négative."))
        ],
        error_messages={
            "invalid": _("Veuillez saisir un entier valide."),
            "blank": _("Ce champ est requis."),
        },
        help_text=_("Entier ≥ 0 et ≤ au nombre de groupes autorisés ")
    )

    def clean(self):
        #Validation inter-champs : s'assure que Entreprise_Num_Customer_Create ≤ Entreprise_Num_Customer_Allow
        super().clean()
        max_allowed = self.Entreprise_Num_Customer_Allow
        # Si le plafond est absent, on bloque (
        if max_allowed is None:
            raise ValidationError({
                "Entreprise_Num_Customer_Allow": _("Le nombre de client autorisé doit être défini.")
            })

        # Vérifie la borne supérieure dynamique
        if self.Entreprise_Num_Customer_Create is not None and self.Entreprise_Num_Customer_Create > max_allowed:
            raise ValidationError({
                "Entreprise_Num_Customer_Create": _("La valeur ne peut pas dépasser %(max)s.") % {"max": max_allowed}
            })

        #Validation inter-champs : s'assure que Entreprise_Num_User_Create ≤ Entreprise_Num_User_Allow
        super().clean()
        max_allowed = self.Entreprise_Num_User_Allow
        # Si le plafond est absent, on bloque (
        if max_allowed is None:
            raise ValidationError({
                "Entreprise_Num_User_Allow": _("Le nombre d'utilisateur autorisé doit être défini.")
            })

        # Vérifie la borne supérieure dynamique
        if self.Entreprise_Num_User_Create is not None and self.Entreprise_Num_User_Create > max_allowed:
            raise ValidationError({
                "Entreprise_Num_User_Create": _("La valeur ne peut pas dépasser %(max)s.") % {"max": max_allowed}
            })      

        #Validation inter-champs : s'assure que Entreprise_Num_Supervisor_Create ≤ Entreprise_Num_Supervisor_Allow
        super().clean()
        max_allowed = self.Entreprise_Num_Supervisor_Allow
        # Si le plafond est absent, on bloque (
        if max_allowed is None:
            raise ValidationError({
                "Entreprise_Num_Superviseur_Allow": _("Le nombre de superviseur autorisé doit être défini.")
            })

        # Vérifie la borne supérieure dynamique
        if self.Entreprise_Num_Supervisor_Create is not None and self.Entreprise_Num_Supervisor_Create > max_allowed:
            raise ValidationError({
                "Entreprise_Num_Supervisor_Create": _("La valeur ne peut pas dépasser %(max)s.") % {"max": max_allowed}
            })  

        #Validation inter-champs : s'assure que Entreprise_Num_Group_Create ≤ Entreprise_Num_Group_Allow
        super().clean()
        max_allowed = self.Entreprise_Num_Group_Allow
        # Si le plafond est absent, on bloque (
        if max_allowed is None:
            raise ValidationError({
                "Entreprise_Num_Group_Allow": _("Le nombre de groupe autorisé doit être défini.")
            })

        # Vérifie la borne supérieure dynamique
        if self.Entreprise_Num_Group_Create is not None and self.Entreprise_Num_Group_Create > max_allowed:
            raise ValidationError({
                "Entreprise_Num_Group_Create": _("La valeur ne peut pas dépasser %(max)s.") % {"max": max_allowed}
            }) 
        
    class Meta:
        # Contrainte SQL ajoutées à la BDD : robustesse même pour les écritures hors Django
        
      constraints = [

            # contraintes pour Entreprise_Num_Customer_Allow
            models.CheckConstraint(
                check=Q(Entreprise_Num_Customer_Allow__gte=0) & Q(Entreprise_Num_Customer_Allow__lte=999),
                name="chk_allow_between_0_and_999",
            ),

            # contraintes pour Entreprise_Num_Customer_Create
            models.CheckConstraint(
                check=Q(Entreprise_Num_Customer_Create__gte=0) & Q(Entreprise_Num_Customer_Create__lte=F("Entreprise_Num_Customer_Allow")),
                name="chk_customer_create_lte_allow",
            ),

            # contraintes pour Entreprise_Num_User_Create
            models.CheckConstraint(
                check=Q(Entreprise_Num_User_Create__gte=0) & Q(Entreprise_Num_User_Create__lte=F("Entreprise_Num_User_Allow")),
                name="chk_user_create_lte_allow",
            ),

            # contraintes pour Entreprise_Num_Supervisor_Create
            models.CheckConstraint(
                check=Q(Entreprise_Num_Supervisor_Create__gte=0) & Q(Entreprise_Num_Supervisor_Create__lte=F("Entreprise_Num_Supervisor_Allow")),
                name="chk_supervisor_create_lte_allow",
            ),

            # contraintes pour Entreprise_Num_Group_Create
            models.CheckConstraint(
                check=Q(Entreprise_Num_Group_Create__gte=0) & Q(Entreprise_Num_Group_Create__lte=F("Entreprise_Num_Group_Allow")),
                name="chk_group_create_lte_allow",
            ),
        ]

##############################
# Surcharge de la table User #
##############################
class Compte(User) :
    #Entreprise de ratachement (Impossible de supprimer l'Entreprise si un compte est encore lié)
    Compte_IDEntreprise = models.ForeignKey(Entreprise, on_delete = models.PROTECT)

    #Image de profil
    Compte_Image = models.ImageField(upload_to='SKM_Pictures/Profile', default='SKM_Pictures/Profile/default.png')

#####################################
# Création des éléments par défault #
#####################################
@receiver(post_migrate)
def create_default_groups(sender, **kwargs) :

    # Création des groupes d'utilisateurs
    for name in DEFAULT_GROUPS :
        group, created = Group.objects.get_or_create(name=name)
        if created:
            print(f"Groupe d'utilisateurs par défault créé: {name}")