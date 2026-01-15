from django.shortcuts import render,redirect

from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from SKT_account.models import Entreprise, Compte

from django.contrib.auth.models import Group


from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import UserCreateForm

# Variables globales
from django.conf import settings

# Pour l'encodage du Token
import hmac, hashlib, base64, time 
from urllib.parse import urlencode


# Create your views here.

@staff_member_required
def create_user_view(request):
    """
    Vue protégée : seuls les membres du staff peuvent créer un utilisateur.
    """
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Utilisateur créé : {user.email}")
            # Récupérer le groupe "Administrator"
            admin_group = Group.objects.get(name="Administrator")

            # Liste des utilisateurs dans ce groupe
            users_in_admin_group = admin_group.user_set.all()
            return render(request, "users_manage.html", {'users': users_in_admin_group})  
    else:
        form = UserCreateForm()

    return render(request, "create_user.html", {"form": form})

# Génération du TOKEN et de l'URL pour appel de l'app
def generate_secure_url(IDUser, URL):
	#récupération de l’heure
	timestamp = str(int(time.time()))

    #création du message à encoder (IDUser et heure)
	message = f"{IDUser}|{timestamp}"

	#création de la signature à partir de la clé secrète et du message
	signature = hmac.new(settings.SKT_SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

	#création du token complet 
	token_raw = f"{message}|{signature}"

	#encodage du token
	token_b64 = base64.urlsafe_b64encode(token_raw.encode()).decode()

	#renvoi de l’URL complète
	return f"https://{URL}?token={token_b64}"

def connectionHandler(request) :

    #récupération de l'utilisateur connecté
    email = request.POST.get('username')
    pwd = request.POST.get('password')
    user = authenticate(request, username = email, password = pwd) 

    #vérification de l'authenification
    if not user :
        raise PermissionDenied(_("Utilisateur non authentifié."))

    #si c'est un SuperAdministrateur
    if user.is_authenticated and user.is_staff and user.is_active :
            
            # Récupérer le groupe "Administrator"
            admin_group = Group.objects.get(name="Administrator")

            # Liste des utilisateurs dans ce groupe
            users_in_admin_group = admin_group.user_set.all()
           
            return render(
                request,
                'users_manage.html',
                {'users': users_in_admin_group}
            )        

    #si c'est un Administrateur
    if user.is_authenticated and user.groups.first().name=="Administrator" and user.is_active :
            
            # Liste des entreprises
            entreprises = Entreprise.objects.all()
           
            return render(
                request,
                'entreprises_manage.html',
                {'entreprises': entreprises}
            )
 
    # récupération de l'entreprise
    compte = Compte.objects.filter(id = user.id).first()
    if compte :
        entreprise = compte.Compte_IDEntreprise
    else :
        raise PermissionDenied(_("Utilisateur non affecté à une entreprise"))
    
    # Comparaison avec la date du jour (UTC par défaut, convertie en date)
    today = timezone.now().date()

    # Vérification de la définition d'une date de début de licence
    if not entreprise or entreprise.Entreprise_Licence_Date_Start is None:
        raise PermissionDenied(_("Aucune date de licence définie pour l'entreprise."))

    # Vérification de la validité de la licence
    licence = False
    # La licence est active
    if entreprise.Entreprise_Licence_Statut == 'ACT' :
        #La période de licence a démarré
        if entreprise.Entreprise_Licence_Date_Start <= today :
            #La période de licence n'est pas finie
            if entreprise.Entreprise_Licence_Date_End is None or entreprise.Entreprise_Licence_Date_End > today :
                licence = True

    if not licence :
        raise PermissionDenied(_("La licence est invalide"))

    #traitement en fonction du groupe de l'utilisateur
    match user.groups.first().name:
        case "SKT_User":
            url = generate_secure_url(user.id, settings.SKT_URL_WEBAPP)
            return redirect(url)
        case "Customer":
            print("Client")
        case "Supervisor":
            print("Supervisor")
        case _:
            raise PermissionDenied(_("Le rôle de l'utilisateur n'est pas défini"))

    return render(
        request,
        'base.html',
    )


 
