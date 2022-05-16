Automatically books an appointment for a covid vaccine on Doctolib. Developed and used in the days when doses were restricted and announced at the last moment 

# Prérequis
- Installer Chrome
- Activer le son de l'ordinateur (volume maximum car l'alerte n'est pas élevée)
- Avoir un compte Doctolib, avec un mot de passe ne contenant pas de caractères spéciaux
- Télécharger la dernière release [autodoser.exe](https://github.com/M07ak/auto_doctolib_doser/releases/download/1.0.2/autodoser.zip)

# Préparation
- Ouvrir le fichier infos.json
- Remplir le nom d'utilisateur doctolib (en gardant les guillemets autour du texte)
- Remplir le mot de passe doctolib (en gardant les guillemets autour du texte)
- Renseigner la ville ciblée pour faire les recherches
- Renseigner la distance maximul à laquelle le programme cherchera des doses (en km, calculé à vol d'oiseau). 10 fonctionne bien à Rennes pour avoir uniquement les centres dans la ville
- Renseigner sa latitude (Vérifier avec Google maps en faisant un clic droit sur le point)
- Renseigner sa longitude
- Sauvegarder

# Lancement
- Double cliquer sur auto_dose_doctolib.exe
- Le programme va d'abord se connecter à Doctolib, pour gagner du temps
- Puis il cherche tous les centre autour de la ville, et filtre les centres avec la distance maximum renseignée
- Enfin, il scan automatiquement 2 fois / seconde chaque centre qu'il a trouvé
- Il faut garder Google Chrome ouvert avec la taille la plus grande possible

# Une dose est trouvée
- Le programme ouvre la page du centre concerné et présélectionne la dose. Vous devez alors finir la processus de réservation de la dose, en allant le plus vite possible (moins de 5 secondes)
- Le programme emet un bip en continu, toutes les secondes,
- En cas d'échec, cliquer sur l'invite de commande, et appuyer sur entrée pour reprendre les recherches

# Problème possible
- Windows détecte le programme comme un virus
- Cliquer sur la notification Windows Defender, et ignorer la fichier
- Le fichier peut être supprimé par l'antivirus, il faut alors le re télécharger
