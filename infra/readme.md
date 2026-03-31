chall48h-25-26 - README

Description :
--------------
"chall48h-25-26" est un dashboard web développé en Python avec Uvicorn. 
Il permet d'afficher différentes informations interactives via une interface web.
Le projet est conçu pour être déployé facilement avec Docker.

Prérequis :
-------------
- Docker installé sur la machine
- Git pour cloner le projet
- Accès réseau pour naviguer vers le dashboard
- Python 3.11+ si vous voulez lancer le projet sans Docker

Installation :
--------------
1. Cloner le projet depuis GitHub :
   git clone https://github.com/<TON_UTILISATEUR>/chall48h-25-26.git
   cd chall48h-25-26

2. Construire l'image Docker (Dockerfile dans infra/) :
   docker build -t chall48h-25-26 ./infra

Lancement avec Docker :
-----------------------
Pour lancer le dashboard :
   docker stop chall48h-25-26 2>/dev/null
   docker rm chall48h-25-26 2>/dev/null
   docker run -d -p 8080:8000 --name chall48h-25-26 chall48h-25-26

Accès :
   http://<IP_DU_SERVEUR>:8080

Relance rapide avec script :
----------------------------
Un script relaunch.sh est fourni pour relancer le container facilement :
   chmod +x relaunch.sh
   ./relaunch.sh

Lancement sans Docker (optionnel) :
-----------------------------------
Si vous voulez lancer le dashboard directement avec Python :
   cd app
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 8000

Accès :
   http://<IP_DU_SERVEUR>:8000

Organisation du projet :
-----------------------
chall48h-25-26/
│
├─ app/                # Code Python du dashboard
│  └─ main.py          # Point d’entrée de l’application
│
├─ infra/              # Contient le Dockerfile
│  └─ Dockerfile
│
├─ relaunch.sh         # Script pour relancer le container
├─ requirements.txt    # Dépendances Python
└─ README.txt          # Ce fichier

HTTPS avec DuckDNS et Traefik (optionnel) :
-------------------------------------------
1. Créez un domaine gratuit DuckDNS (ex : monsite.duckdns.org).
2. Installez Traefik via Docker Compose.
3. Configurez le Docker Compose pour exposer votre service dashboard
   via Traefik avec le label `traefik.http.routers.dashboard.rule=Host("monsite.duckdns.org")`
   et `traefik.http.routers.dashboard.tls=true`.
4. Relancez Traefik et le container du dashboard.
5. Accédez ensuite via : https://monsite.duckdns.org

Notes :
-------
- Le dashboard fonctionne actuellement en HTTP si vous ne configurez pas Traefik.
- Assurez-vous que le port 8080 n’est pas utilisé par un autre service.
- Traefik / HTTPS est optionnel et peut être ajouté plus tard.

Auteur :
--------
- <TON NOM / PSEUDO>
- Projet développé dans le cadre d’un challenge interne ou projet personnel.
