import json, os
from uuid import uuid4
from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from jinja2 import Environment, FileSystemLoader

app = FastAPI()
env = Environment(loader=FileSystemLoader("templates"))
app.mount("/static", StaticFiles(directory="static"), name="static")

# Répertoire principal pour les uploads (doit être un dossier existant)
BASE_UPLOAD_DIRECTORY = "static/uploads"

# Répertoire pour sauvegarder les photos de profil
USER_PHOTO_DIRECTORY = "static/users"
os.makedirs(USER_PHOTO_DIRECTORY, exist_ok=True)  # Crée le dossier si nécessaire

# Vérifier si le répertoire principal existe
if not os.path.exists(BASE_UPLOAD_DIRECTORY):
    raise RuntimeError(f"Le répertoire {BASE_UPLOAD_DIRECTORY} n'existe pas.")

# Fichier JSON pour stocker les données
data_files = {
    "familles": "data/familles.json",
    "logements": "data/logements.json"
}

def chargement(file):
    with open(file, 'r', encoding="UTF-8") as f:
        data: list | dict = json.load(f)

    return data


def uploading(data):
    with open('data/user.json', 'w', encoding="UTF-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Fonction pour sauvegarder les données dans un fichier JSON
def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_file(file: UploadFile, group_directory: str) -> str:
    # Générer un nom unique pour éviter les conflits
    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(group_directory, unique_filename)

    # Vérifier le type de fichier (accepter uniquement les images .jpg, .png, .jpeg)
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail=f"Format de fichier non valide pour {file.filename}. Seuls .jpg, .jpeg, .png sont autorisés.")

    # Sauvegarder le fichier sur le serveur
    with open(file_path, "wb") as f:
        f.write(file.file.read())  # Écrit le contenu du fichier
    relative_path = file_path.split("static/", 1)[-1]  # Extrait tout ce qui vient après "static/"
    return relative_path # Retourne le chemin d'accès au fichier sauvegardé

def save_profile_photo(photo: UploadFile, username: str) -> str:
    # Valider le type de fichier
    if not photo.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise ValueError("Format de fichier invalide. Seuls les fichiers .jpg, .jpeg et .png sont acceptés.")

    # Construire le chemin complet pour la photo de profil
    filename = f"{username}{os.path.splitext(photo.filename)[-1]}"  # username + extension du fichier
    file_path = os.path.join(USER_PHOTO_DIRECTORY, filename)

    # Sauvegarder le fichier sur le serveur
    with open(file_path, "wb") as f:
        f.write(photo.file.read())

    return filename



@app.get("/", response_class=HTMLResponse)
def show_index_page(request: Request):
    template = env.get_template('index.html')
    cookie = request.cookies.get("user")
    message = request.cookies.get("flash-message", "")
    if cookie:
        cookie = json.loads(cookie)
        if not cookie["valide"]:
            reponse = RedirectResponse(url='/userform')
            return reponse
        return template.render(url_for=request.app.url_path_for, user=cookie, message=message, famille={})
    return template.render(url_for=request.app.url_path_for, message=message, famille={})


@app.get("/familyhost", response_class=HTMLResponse)
async def show_host_family_page(request: Request):
    template = env.get_template('familyhost.html')
    data:list = chargement('data/familles.json')
    cookie:str | None = request.cookies.get("user")
    if cookie:
        return template.render(url_for=request.app.url_path_for, familles=data, user=json.loads(cookie))
    return template.render(url_for=request.app.url_path_for, familles=data)



@app.get("/colocataires", response_class=HTMLResponse)
async def show_colocataires_page(request: Request):
    template = env.get_template('colocataire.html')
    data = chargement('data/colocataires.json')
    cookie = request.cookies.get("user", {})
    if cookie:
        return template.render(url_for=request.app.url_path_for, colocataires=data, user=json.loads(cookie))
    return template.render(colocataires=data, url_for=request.app.url_path_for)



@app.get("/logements", response_class=HTMLResponse)
async def show_logements_page(request: Request):
    template = env.get_template('logement.html')
    data = chargement('data/logements.json')
    cookie:str | None = request.cookies.get("user")
    if cookie:
        return template.render(url_for=request.app.url_path_for, logements=data, user=json.loads(cookie))
    return template.render(logements=data, url_for=request.app.url_path_for)



@app.get("/detail", response_class=HTMLResponse)
def show_contact_page(request: Request):

    index = request.query_params.get("index")

    fichier = request.query_params.get("file", "")

    file = ["data/logements.json","data/familles.json", "data/colocataires.json"]

    template = env.get_template('detail.html')

    cookie:str | None = request.cookies.get("user")
    if index and fichier:
        data = chargement(file[int(fichier)])[int(index)]
    else:
        data = {}
    if cookie:
        if fichier == "2":
            template = env.get_template('info_coloc.html')
            return template.render(url_for=request.app.url_path_for, user=json.loads(cookie), item=data)
        return template.render(url_for=request.app.url_path_for, user=json.loads(cookie), item=data)
    if fichier == "2":

        template = env.get_template('info_coloc.html')
        return template.render(url_for=request.app.url_path_for, item=data)
    return template.render(url_for=request.app.url_path_for, item=data)



@app.get("/contact", response_class=HTMLResponse)
def show_contact_page(request: Request):
    template = env.get_template('contact.html')
    cookie:str | None = request.cookies.get("user")
    if cookie:
        return template.render(url_for=request.app.url_path_for, user=json.loads(cookie))
    return template.render(url_for=request.app.url_path_for)



@app.get("/login", response_class=HTMLResponse)
async def show_login_page(request: Request):
    template = env.get_template('login.html')
    cookie:str | None = request.cookies.get("user")
    message = request.cookies.get("flash-message", "")
    if cookie:
        reponse = RedirectResponse(url='/', status_code=302)
        return reponse
    return template.render(url_for=request.app.url_path_for, message=message)



@app.post("/login", response_class=HTMLResponse)
async def show_login_page(username_mail:str = Form(...), password:str = Form(...)):
    users:dict = chargement('data/user.json')
    reponse = RedirectResponse(url="/login", status_code=302)

    for key, user in users.items():
        if (username_mail == user["mail"] or username_mail == user["username"]) and password == user["password"]:
            reponse = RedirectResponse(url='/', status_code=302)
            reponse.set_cookie(key='user', value=json.dumps(user))
            reponse.set_cookie(key="id", value=key)
            reponse.set_cookie(key="flash-message", value=f"Bienvenue {user["prenom"]}", max_age=5)
            if not user['valide']:
                reponse.set_cookie(key="id_user", value=key)
            return reponse
    reponse.set_cookie(key="flash-message", value=f"Identifiant incorrect, veuillez réessayez", max_age=5)
    return reponse



@app.get("/register", response_class=HTMLResponse)
async def show_register_page(request: Request):
    template = env.get_template('register.html')
    cookie:str | None = request.cookies.get("user")
    message = request.cookies.get("flash-message", "")
    if cookie:
        template = RedirectResponse(url='/', status_code=302)
        return template
    return template.render(url_for=request.app.url_path_for, message=message)



@app.post("/register", response_class=HTMLResponse)
async def register_validate(request:Request, firstname:str = Form(...), lastname:str = Form(...),
    username:str = Form(''), mail:str = Form(...), password:str = Form(...), conf_password:str = Form(...)):

    data = chargement('data/user.json')

    for element in data.values():
        if (mail == element["mail"]) or (username == element["username"]):
            reponse = RedirectResponse(url="/register", status_code=302)
            reponse.set_cookie(key="flash-message", value=f"{mail} ou {username} déjà utiliser", max_age=5)
            return reponse


    if password == conf_password:
        ide = str(uuid4())
        user: dict = {
            'perso': (firstname[0]+lastname[0]).upper(),
            'nom': firstname,
            'prenom': lastname,
            'username': username,
            'mail': mail,
            'password': password,
            "valide": 0
        }
        data[ide] = user
        uploading(data)
        reponse = RedirectResponse(url='/userform', status_code=302)
        reponse.set_cookie(key="flash-message", value=f"Inscription réussit veuillez remplir le form pour finaliser !!!", max_age=5)
        reponse.set_cookie(key="id_user", value=ide)
        return reponse
    else:
        reponse = RedirectResponse(url="/register", status_code=302)
        reponse.set_cookie(key="flash-message", value=f"mauvais mot de pass", max_age=5)
        return reponse


@app.get("/userform", response_class=HTMLResponse)
def pos(request:Request):

    cookie:str | None = request.cookies.get("user")
    message = request.cookies.get("flash-message")
    id1 = "y"
    if cookie:
        id1 = json.loads(cookie)["valide"]
    id2 = request.cookies.get("id_user")
    if not id1 or id2:
        template = env.get_template("formuser.html")
        if cookie:
            return template.render(url_for=request.app.url_path_for, message=message, user=json.loads(cookie))
        return template.render(url_for=request.app.url_path_for, message=message)
    return RedirectResponse(url='/', status_code=302)

    # ide = request.cookies.get("id")
    # if ide:
    #     template = env.get_template("formuser.html")
    #     return template.render(url_for=request.app.url_path_for)
    # else:
    #     template = RedirectResponse(url='/', status_code=302)
    #     return template


@app.post("/userform", response_class=HTMLResponse)
async def poste(
        request: Request,
        fonction: str = Form(...),
        age: str = Form(...),
        numero: str = Form(...),
        description: str = Form(...),
        budget: int = Form(...),
        photo_profil: UploadFile = File(...)
):
    # Charger les données des utilisateurs
    data: dict = chargement("data/user.json")
    coloc = chargement('data/colocataires.json')

    # Récupérer le cookie id (si disponible)
    id1 = request.cookies.get("id_user")
    cookie = request.cookies.get("user")

    if id1:
        # Mettre à jour les informations de l'utilisateur
        data[id1]["fonction"] = str(fonction)
        data[id1]["age"] = str(age)
        data[id1]["num"] = str(numero)
        data[id1]["description"] = str(description)
        data[id1]["budget"] = int(budget)
        data[id1]["valide"] = 1

        # Sauvegarder la photo de profil dans "static/users"
        username = data[id1]["username"]
        photo_path = save_profile_photo(photo_profil, username)
        data[id1]["photo"] = "users/"+photo_path

        # Sauvegarder les données mises à jour
        uploading(data)

        data[id1]["contacts"] = {
            "telephone":data[id1]["num"],
            "email":data[id1]["mail"]
        }

        del data[id1]["num"]
        del data[id1]["mail"]
        del data[id1]["password"]

        coloc.append(data[id1])
        save_json('data/colocataires.json', coloc)

        # Rediriger l'utilisateur vers la page de connexion
        reponse = RedirectResponse(url='/login', status_code=302)
        reponse.set_cookie(key="flash-message", value="Inscription réussie, veuillez vous connecter !!!", max_age=5)

        # Si un cookie utilisateur existe, mettre à jour ses informations
        if cookie:
            reponse.set_cookie(key="user", value=json.dumps(data[id1]))
        reponse.delete_cookie("id_user")
        return reponse

    # Redirection si aucun ID utilisateur
    else:
        return RedirectResponse(url='/', status_code=302)



@app.get("/dashboard", response_class=HTMLResponse)
def show_userinfo_page(request: Request):
    cookie:str | None = request.cookies.get("user")
    if cookie:
        cookie:dict = json.loads(cookie)
        template = env.get_template("dashboard.html")
        user_photo_path = cookie['photo']
        return template.render(url_for=request.app.url_path_for, user=cookie, user_photo_path=user_photo_path)
    else:
        reponse = RedirectResponse(url='/', status_code=302)
        return reponse



@app.get("/admin", response_class=HTMLResponse)
def show_userinfo_page(request: Request):
    cookie:str | None = request.cookies.get("user")
    if cookie:
        template = env.get_template("admin.html")
        return template.render(url_for=request.app.url_path_for, user=json.loads(cookie))
    else:
        reponse = RedirectResponse(url='/', status_code=302)
        return reponse


# Route pour gérer la réception des données du formulaire
@app.post("/admin")
async def add_data(
    group: str = Form(...),
    nom: str = Form(...),
    localisation: str = Form(...),
    budget: str = Form(...),
    capacite: str = Form(...),
    contacts: str = Form(...),
    description: str = Form(...),
    customFile: UploadFile = File(...),
    images: List[UploadFile] = File([]),
    extra: Optional[str] = Form(None)
):
    # Vérifier si le groupe est valide
    if group not in data_files:
        raise HTTPException(status_code=400, detail="Groupe invalide")

    # Chemin du répertoire spécifique au groupe
    group_directory = os.path.join(BASE_UPLOAD_DIRECTORY, group)
    os.makedirs(group_directory, exist_ok=True)  # Crée le répertoire s'il n'existe pas

    # Enregistrer l'image principale
    main_image_path = save_file(customFile, group_directory)

    # Enregistrer les images supplémentaires
    additional_images_paths = []
    for image in images:
        if image.filename:  # Vérifie qu'une image a bien été téléchargée
            additional_images_paths.append(save_file(image, group_directory))

    # Créer une structure de données
    new_data = {
        "id": len(load_json(data_files[group])) + 1,  # Génère un ID basé sur les données existantes
        "nom": nom,
        "localisation": localisation,
        "budget": budget,
        "capacite": capacite,
        "contacts": contacts,
        "description": description,
        "main_image": main_image_path,
        "additional_images": additional_images_paths
    }

    # Ajouter des données supplémentaires (extra) si elles existent
    if extra:
        try:
            extra_data = json.loads(extra)
            new_data.update(extra_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Les données supplémentaires doivent être au format JSON valide")

    # Charger les données existantes
    existing_data = load_json(data_files[group])

    # Ajouter les nouvelles données
    existing_data.append(new_data)

    # Sauvegarder dans le fichier JSON
    save_json(data_files[group], existing_data)

    return RedirectResponse(url='/admin', status_code=302)



# Route pour mettre à jour les données utilisateur
@app.post("/updata_data")
async def update_user_data(
    request: Request,
    mail: str = Form(...),
    username: str = Form(...),
    num: str = Form(...),
    fonction: str = Form(...),
    password: str = Form(...),
    photo: UploadFile = File(...)
):
    # Charger les données des utilisateurs
    user_data = chargement('data/user.json')

    # Récupérer l'ID de l'utilisateur connecté depuis les cookies
    user_id = request.cookies.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Utilisateur non connecté.")

    # Vérifier que l'utilisateur existe dans les données
    if user_id not in user_data:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    # Mettre à jour les données de l'utilisateur
    user_data[user_id]["mail"] = mail
    user_data[user_id]["username"] = username
    user_data[user_id]["num"] = num
    user_data[user_id]["fonction"] = fonction
    user_data[user_id]["password"] = password

    # Sauvegarder la photo de profil
    photo_path = save_profile_photo(photo, username)
    user_data[user_id]["photo"] = "users/"+photo_path

    # Enregistrer les données mises à jour
    uploading(user_data)

    # Rediriger vers une page de confirmation ou autre
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.delete_cookie(key="user")
    response.set_cookie(key="user", value=json.dumps(user_data[user_id]))
    response.set_cookie(key="flash-message", value="Données mises à jour avec succès !", max_age=5)
    return response



@app.get('/forgot_password', response_class=HTMLResponse)
def forgot_password(request:Request):
    template = env.get_template('forgot.html')
    return template.render(url_for=request.app.url_path_for)



@app.post('/forgot_password', response_class=HTMLResponse)
def validez_forgot_password(request:Request, username_mail:str = Form(...)):
    data = chargement('data/user.json')
    for key, user in data.items():
        if user['mail'] == username_mail or user['username']:
            reponse = RedirectResponse(url='/reset_password', status_code=302)
            reponse.set_cookie(key='id', value=key)
            return reponse

    return RedirectResponse(url='/', status_code=302)



@app.get('/reset_password', response_class=HTMLResponse)
def show_form(request:Request):
    template = env.get_template('update_password.html')
    return template.render(url_for=request.app.url_path_for)



@app.post('/reset_password', response_class=HTMLResponse)
def form_update_password(request:Request, confirm_password:str = Form(...), new_password:str = Form(...)):
    user_id = request.cookies.get('id')
    data = chargement('data/user.json')
    if user_id:
        if new_password == confirm_password:
            data[user_id]['password'] = confirm_password
            uploading(data)
            reponse = RedirectResponse('/login', status_code=302)
            reponse.set_cookie(key="flash-message", value="Données mises à jour avec succès !", max_age=60)
            return reponse
        else:
            reponse = RedirectResponse('/reset_password', status_code=302)
            reponse.set_cookie(key="flash-message", value="Données invalide veuillez réessayer", max_age=60)
            return reponse
    return RedirectResponse(url='/', status_code=302)



@app.post('/contact', response_class=HTMLResponse)
def send_message(request:Request, nom:str = Form(...), mail:str = Form(...), message:str = Form(...)):
    data = chargement('data/message.json')
    message_user: dict = {
        'nom': nom,
        'mail': mail,
        'message': message,
    }
    data.append(message_user)
    save_json(file_path='data/message.json', data=data)
    reponse = RedirectResponse(url='/', status_code=302)
    reponse.set_cookie(key="flash-message", value="Message envoyer avec succès !!!", max_age=5)
    return reponse



@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    reponse = RedirectResponse(url='/', status_code=302)
    reponse.delete_cookie("user")
    reponse.delete_cookie("id_user")
    reponse.delete_cookie("id")
    return reponse


# Route de test pour vérifier les données enregistrées
@app.get("/admin/{group}")
async def get_data(group: str):
    if group not in data_files:
        raise HTTPException(status_code=400, detail="Groupe invalide")
    return load_json(data_files[group])
