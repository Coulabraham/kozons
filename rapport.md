# Rapport de suivi du projet Kozons

Ce document centralise le suivi de tout le travail réalisé sur le projet. Il sera mis à jour au fil des interventions afin de conserver une trace claire des actions, des décisions, des difficultés, des solutions et des vérifications.

## Sommaire

- [Règles de suivi](#regles)
- [11 septembre 2026 — Mise en place du rapport de suivi](#rapport-initial)
- [11 septembre 2026 — Schéma de données de la messagerie](#schema-donnees)
- [11 septembre 2026 — Construction du backend Django temps réel](#backend)
- [11 septembre 2026 — Construction du frontend PWA Next.js](#frontend)
- [11 septembre 2026 — Lancement local du frontend](#lancement)
- [12 septembre 2026 — Audit et durcissement de sécurité](#securite)
- [12 septembre 2026 — Logo, données fictives et accueil](#logo-donnees)
- [12 septembre 2026 — Correction de Failed to fetch](#failed-to-fetch)
- [12 septembre 2026 — Résolution de l’absence d’OTP reçu](#otp-local)
- [12 septembre 2026 — Accès depuis un autre appareil et activation OTP](#reseau-otp)
- [12 septembre 2026 — Messagerie avancée, groupes, multi-appareils et notifications iOS](#messagerie-avancee)

<a id="regles"></a>

## Règles de suivi

Chaque intervention devra préciser, selon les besoins :

- la date et l’objectif de l’intervention ;
- les fichiers consultés, créés ou modifiés ;
- les actions réalisées et les choix techniques effectués ;
- les difficultés, erreurs ou risques rencontrés ;
- les solutions appliquées ou proposées ;
- les commandes, tests et vérifications exécutés ;
- le résultat final et les éventuels travaux restant à faire.

Les difficultés seront consignées même lorsqu’elles sont rapidement résolues. Si aucune difficulté n’est rencontrée, cela sera également indiqué. Aucun secret, mot de passe, jeton d’accès ou autre renseignement sensible ne devra être copié dans ce rapport.

---

<a id="rapport-initial"></a>

## 11 septembre 2026 — Mise en place du rapport de suivi

### Objectif

Créer un rapport permanent recensant l’ensemble du travail effectué sur le projet Kozons, ainsi que les difficultés rencontrées et les solutions retenues.

### État initial observé

- Le dossier du projet contenait uniquement le fichier `rapport.md`.
- Le contenu initial de ce fichier était : « ici sera mis le rapport de tout ce qui sera fait sur le projet Kozons. »
- Aucun fichier `AGENTS.md` contenant des consignes supplémentaires n’a été trouvé.
- Le dossier n’était pas initialisé comme dépôt Git au moment de la vérification.

### Actions réalisées

- Inspection non destructive du contenu du dossier.
- Lecture du contenu initial de `rapport.md`.
- Remplacement de la note initiale par une structure de rapport durable et cumulative.
- Définition des informations à consigner lors des prochaines interventions.

### Difficultés rencontrées

La commande d’inspection groupée a retourné un code d’erreur parce que le dossier n’est pas un dépôt Git. Cette erreur n’a causé aucune modification ni perte de données.

### Solution appliquée

Le résultat de chaque vérification a été interprété séparément : l’absence de dépôt Git a été enregistrée comme un élément de l’état initial, sans tenter d’initialiser Git puisque cela n’avait pas été demandé.

### Vérifications

- Le contenu existant a été lu avant toute modification.
- Aucun autre fichier du projet n’a été modifié.
- La présence du rapport dans le dossier racine a été confirmée.

### Résultat

Le fichier `rapport.md` constitue désormais le journal de suivi du projet. Il devra être enrichi à chaque nouvelle intervention.

---

<a id="schema-donnees"></a>

## 11 septembre 2026 — Schéma de données de la messagerie

### Objectif

Concevoir et implémenter le modèle relationnel PostgreSQL de Kozons pour les conversations individuelles et de groupe, les messages texte, les notes vocales, les images et les vidéos. Définir également les structures Redis, l’organisation du stockage objet, la pagination à grande échelle et une stratégie d’archivage.

### État initial

Le projet ne contenait aucun code applicatif ni configuration Django. Seul le présent rapport existait. Le choix a donc été de créer une application Django autonome nommée `messagerie`, intégrable ensuite à un projet Django principal par `INSTALLED_APPS`.

### Fichiers créés

- `.gitignore` : exclusion des caches Python, environnements virtuels, bases SQLite locales et fichiers d’environnement sensibles.
- `messagerie/__init__.py` : déclaration du paquet Python.
- `messagerie/apps.py` : configuration de l’application Django.
- `messagerie/models.py` : modèles, relations, validations, contraintes et index.
- `messagerie/migrations/__init__.py` : déclaration du paquet de migrations.
- `messagerie/migrations/0001_initial.py` : migration initiale créant les six tables PostgreSQL.
- `messagerie/fixtures/kozons_seed.json` : données de test réalistes.
- `messagerie/README.md` : documentation d’intégration, d’exploitation et de performance.

### Modèle implémenté

- `utilisateur` : identifiant `BIGINT`, téléphone et email uniques et facultatifs, avec obligation d’en renseigner au moins un ; mot de passe haché, profil, état, dernière connexion et date de création.
- `contact` : deux clés étrangères vers les utilisateurs, unicité du couple propriétaire/contact et interdiction de s’ajouter soi-même.
- `conversation` : type contrôlé (`individuel` ou `groupe`), créateur protégé contre une suppression physique et nom obligatoire pour un groupe.
- `membre_conversation` : unicité du couple conversation/utilisateur et rôles contrôlés (`membre`, `admin`, `proprietaire`).
- `message` : type contrôlé, cohérence entre contenu et média, durée positive et obligatoire pour les notes vocales.
- `statut_message` : état contrôlé (`envoye`, `recu`, `lu`) et unicité du couple message/utilisateur.

Les clés étrangères sont indexées automatiquement par Django. Les contraintes uniques composites produisent les index uniques demandés.

### Décisions de performance

- Utilisation de `BIGINT` pour éviter l’épuisement des identifiants dans un système à fort volume d’écriture.
- Index `message_conv_date_id_idx` sur `(id_conversation, date_envoi DESC, id DESC)`.
- Ajout de `id` à l’index demandé afin de départager les messages partageant le même horodatage et de fournir une pagination stable.
- Pagination par curseur à partir du couple `(date_envoi, id)`, sans `OFFSET`.
- Taille de page recommandée : 50 à 100 messages.
- Documentation d’une transition vers des partitions mensuelles ou vers un archivage chaud/froid lorsque le volume atteint plusieurs dizaines de millions de messages.

### Difficulté de partitionnement identifiée

PostgreSQL impose que toute clé primaire ou contrainte unique d’une table partitionnée contienne la clé de partition. Une table `message` partitionnée par `date_envoi` ne peut donc pas conserver une clé primaire globale portant uniquement sur `id`.

### Solution proposée

Deux stratégies ont été documentées :

1. adopter une clé primaire composite `(date_envoi, id)` et propager `date_envoi` dans la clé étrangère de `statut_message` lors d’une migration de grande volumétrie ;
2. conserver le schéma actuel et déplacer les données froides dans une table d’archive séparée si l’identifiant global seul doit rester la clé primaire.

La seconde stratégie est la moins intrusive. Une procédure de migration en ligne par copie en lots et bascule atomique a été recommandée afin d’éviter le verrouillage prolongé d’une table massive.

### Structures Redis définies

- Présence par utilisateur dans une clé JSON avec expiration de 60 secondes et heartbeat toutes les 20 secondes ; un `ZSET` complémentaire est prévu pour les connexions multi-appareils.
- Membres actifs d’une conversation dans un `SET` avec expiration de 300 secondes, reconstruction depuis PostgreSQL et invalidation lors d’un changement de membres.
- Compteurs OTP et connexion avec `INCR` et `EXPIRE` atomiques, limitation combinée par identité et par IP, et HMAC des identifiants pour ne pas exposer de téléphone ou d’email dans les clés.
- Préfixage de toutes les clés par application, environnement et version.

### Stockage objet défini

- Organisation par environnement, conversation opaque, type de média, année et mois.
- Nom d’objet en UUIDv7 afin d’éviter les collisions et de conserver une certaine localité temporelle.
- Aucun nom original, téléphone, email ou nom d’utilisateur dans les chemins.
- Références `s3://` conservées en base et génération d’URL signées courtes à la lecture.
- Recommandations sur les types MIME autorisés, la taille, le chiffrement, le transcodage, l’analyse antivirus et les règles de cycle de vie.

### Jeu de données créé

Le seed comprend :

- 4 utilisateurs avec différents cas téléphone/email ;
- 4 relations de contact ;
- 2 conversations individuelles et 1 groupe ;
- 8 adhésions avec plusieurs rôles ;
- 6 messages couvrant texte, note vocale, image et vidéo ;
- 9 états de livraison ou de lecture.

Les domaines et médias du seed sont fictifs. Le mot de passe commun est réservé au développement et est stocké sous forme de hachage PBKDF2.

### Difficultés rencontrées pendant les vérifications

1. Le client `psql` n’est pas installé dans l’environnement local. Il n’a donc pas été possible d’exécuter la migration contre une instance PostgreSQL réelle.
2. La première génération hors connexion du SQL PostgreSQL a échoué, car la méthode interne Django `load_disk()` remplit `disk_migrations` sans retourner le dictionnaire attendu.
3. Lors de la deuxième tentative, l’index des messages semblait absent parce que le contrôle avait lieu avant la fermeture du gestionnaire de schéma, alors que Django génère les index différés à la fermeture.
4. La compilation Python a créé des dossiers `__pycache__` temporaires.

### Solutions appliquées

1. La migration a d’abord été exécutée intégralement sur une base temporaire en mémoire pour valider les relations, contraintes compatibles et données du seed.
2. Le contrôle PostgreSQL hors connexion a été corrigé en lisant `loader.disk_migrations`.
3. La vérification du SQL collecté a été déplacée après la fermeture du gestionnaire de schéma Django.
4. Les caches Python générés ont été supprimés et ajoutés à `.gitignore`.

### Vérifications exécutées

- Compilation de tous les modules Python : réussie.
- `makemigrations --check --dry-run` : aucune modification de migration manquante.
- Application de la migration sur une base temporaire : réussie.
- Chargement du fixture : réussi.
- Comptage après chargement : 4 utilisateurs, 4 contacts, 3 conversations, 8 membres, 6 messages et 9 statuts.
- Génération du SQL avec le backend Django PostgreSQL : 27 instructions produites.
- Présence dans le SQL des six tables, de l’index de pagination et des trois contraintes uniques composites : confirmée.

### Résultat

Le schéma Django demandé, la migration initiale, le seed et la documentation d’architecture sont prêts. La seule vérification restante avant mise en production est un test d’intégration sur une véritable instance PostgreSQL, accompagné d’un `EXPLAIN (ANALYZE, BUFFERS)` sur la requête de pagination avec un volume représentatif.

---

<a id="backend"></a>

## 11 septembre 2026 — Construction du backend Django temps réel

### Objectif

Transformer le schéma de données initial en un backend complet pour Kozons avec Django REST Framework, JWT, Channels, Redis, Celery, stockage S3 présigné, FFmpeg, OTP, SMS interchangeable et notifications Web Push.

### Audit de départ

- Le dépôt contenait uniquement le rapport et l’application de schéma monolithique `messagerie` créée lors de l’intervention précédente.
- Python 3.14.7, Django 5.2.5, Django REST Framework 3.16.1 et psycopg 3.2.13 étaient disponibles.
- Channels, Channels Redis, Celery, SimpleJWT, boto3, pywebpush et le serveur Redis n’étaient pas initialement installés.
- Les exécutables PostgreSQL `psql`, Redis, FFmpeg et Docker n’étaient pas disponibles localement.

### Architecture créée

L’ancienne application `messagerie` a été remplacée par les six applications demandées :

- `users` pour le modèle utilisateur personnalisé, les OTP et l’authentification ;
- `contacts` pour la synchronisation unidirectionnelle du carnet d’adresses ;
- `conversations` pour les conversations et appartenances ;
- `messaging` pour les messages, statuts, historique et WebSocket ;
- `media` pour les uploads S3 et les traitements FFmpeg ;
- `notifications` pour les abonnements et notifications Web Push VAPID.

Les opérations métier sont placées dans des modules `services.py`. Les requêtes de lecture élaborées sont placées dans `selectors.py`. Les vues restent limitées à la validation des entrées, l’appel du service et la sérialisation de la réponse.

### Configuration générale

- Création de `manage.py` et du paquet de projet `kozons`.
- Séparation des réglages en `kozons/settings/base.py`, `dev.py`, `prod.py` et `test.py`.
- Création d’une entrée WSGI dédiée au trafic HTTP classique.
- Création d’une entrée ASGI utilisant `ProtocolTypeRouter` pour Django HTTP et Channels WebSocket.
- Ajout de Celery avec découverte automatique des tâches.
- Configuration de PostgreSQL par `DATABASE_URL`.
- Configuration de quatre bases Redis logiques pour Channels, cache, broker Celery et résultats.
- Configuration JWT avec access court, refresh de trente jours, rotation et blacklist.
- Vérifications de production imposant une clé secrète et une URL PostgreSQL explicites.
- Création de `.env.example`, `requirements.txt`, `pytest.ini`, `Dockerfile`, `.dockerignore` et `docker-compose.yml`.

### Processus de déploiement séparés

- Le service `http` exécute Gunicorn sur `kozons.wsgi` pour `/api/`.
- Le service `realtime` exécute Daphne sur `kozons.asgi` pour `/ws/`.
- Le service `worker` exécute Celery et dispose de FFmpeg dans l’image.
- Le fichier Docker Compose fournit également PostgreSQL, Redis et MinIO.
- La configuration attend qu’un proxy inverse dirige les routes HTTP et WebSocket vers le bon processus.

### Utilisateurs, OTP et JWT

- Modèle `User` basé sur `AbstractBaseUser` et `PermissionsMixin`.
- Téléphone et email facultatifs individuellement, mais contrainte exigeant au moins l’un des deux.
- Normalisation des emails en minuscules et des téléphones au format E.164 avec `phonenumbers`.
- Stockage du mot de passe via les hashers Django dans la colonne `mot_de_passe_hash`.
- Compte inactif jusqu’à validation de l’OTP.
- OTP à six chiffres stocké uniquement sous forme hachée, expirant après cinq minutes et limité à cinq essais.
- Limitation des inscriptions, validations OTP et connexions par compteur de cache avec identifiant HMAC plutôt qu’en clair.
- Connexion possible par téléphone ou email et génération manuelle des tokens SimpleJWT après contrôle de l’état actif.
- Rotation et blacklist des refresh tokens.
- Fournisseurs SMS implémentés derrière une interface commune : console de développement, Twilio et Africa’s Talking.
- Envoi par email lorsque l’inscription ne contient pas de téléphone.

### Contacts

- Endpoint acceptant jusqu’à 1 000 numéros.
- Normalisation, suppression des doublons et exclusion de l’utilisateur courant.
- Recherche uniquement des comptes actifs déjà inscrits.
- Création en masse des contacts trouvés avec `ignore_conflicts`.
- Relation volontairement unidirectionnelle sans demande de confirmation mutuelle.

### Conversations

- Conversations individuelles et de groupe.
- Rôles `admin` et `membre`.
- Limite de 256 membres.
- Le créateur devient administrateur.
- Le groupe exige un nom.
- Une clé SHA-256 déterministe calculée à partir des deux identifiants empêche les doublons de conversations individuelles.
- La création individuelle utilise `get_or_create` afin de mieux résister aux requêtes concurrentes.
- Cache de cinq minutes des membres actifs avec invalidation lors de la création ou d’un futur changement d’appartenance.

### Messagerie REST

- Endpoint d’historique protégé par l’appartenance à la conversation.
- Pagination DRF par curseur sur `(-date_envoi, -id)` avec pages de 50 et maximum de 100.
- Index PostgreSQL correspondant sur `(id_conversation, date_envoi DESC, id DESC)`.
- Endpoint POST REST de repli en complément du WebSocket.
- Champ `client_id` UUID et contrainte unique conditionnelle pour rendre les nouvelles tentatives d’envoi idempotentes.
- Validation des charges utiles en service et par contraintes PostgreSQL.
- Création en masse d’un accusé `envoye` pour chaque destinataire.
- Progression monotone des états `envoye`, `recu`, puis `lu`.

### Temps réel Channels

Un consumer par conversation a été retenu. Ce choix aligne directement le groupe Redis et le périmètre d’autorisation : une connexion est acceptée uniquement après validation du JWT et vérification de l’appartenance à la conversation.

Le consumer traite :

- `message.send` ;
- `receipt.update` ;
- `typing` ;
- `presence.heartbeat`.

Il diffuse avec `group_send` :

- `message.new` ;
- `receipt.updated` ;
- `typing.changed` ;
- `presence.changed`.

Le middleware JWT accepte l’en-tête `Authorization` et, pour les clients navigateur qui ne peuvent pas le fournir, le paramètre `token` de la chaîne de requête. La documentation recommande l’en-tête lorsqu’il est disponible afin de réduire le risque de journalisation du token.

### Présence Redis

- Une clé synthétique de présence expire après 60 secondes.
- Chaque connexion WebSocket possède une entrée dans un `ZSET` avec son horodatage d’expiration.
- Le heartbeat renouvelle la connexion et nettoie les entrées périmées.
- Une déconnexion ne met l’utilisateur hors ligne que si aucune autre connexion active ne reste.
- Le champ PostgreSQL `en_ligne` sert seulement d’instantané ; Redis reste la source temps réel.
- Le réglage de test remplace Redis par un cache local.

### Médias S3

- Modèle `MediaAsset` suivant les états attente, uploadé, traitement, prêt et échec.
- Types autorisés : image, vidéo et note vocale.
- Listes MIME strictes et limites de 20 Mio pour une image, 250 Mio pour une vidéo et 30 Mio pour une note vocale.
- Génération de formulaires POST présignés avec conditions de type et de taille.
- Vérification `HeadObject` après notification de fin d’upload.
- Chemins opaques basés sur HMAC et UUID, sans téléphone, email ni nom original.
- Un message média référence un `media_asset_id` prêt et appartenant à la même conversation ; le client ne peut pas injecter arbitrairement une URL média.
- La référence persistée prend la forme `s3://bucket/key` et le champ `media_url` est donc un `CharField`, pas un validateur limité à HTTP/HTTPS.

### Traitements FFmpeg

- Téléchargement temporaire de l’objet source depuis S3.
- Vidéo convertie en H.264/AAC MP4 avec largeur maximale de 1 280 pixels, CRF 27 et optimisation `faststart`.
- Génération d’une miniature JPEG pour la vidéo.
- Note vocale convertie en Opus mono à 48 kbit/s dans un conteneur OGG.
- Upload des résultats dans le préfixe `processed`.
- Utilisation de `subprocess.run` avec liste d’arguments, délai maximal et sans `shell=True`.
- État d’échec enregistré et tâche Celery réessayée avec délai exponentiel.
- Répertoires temporaires automatiquement nettoyés.

### Notifications push

- Modèle d’abonnement contenant endpoint, clés Web Push et état actif.
- Enregistrement ou mise à jour d’un abonnement par service.
- Tâche Celery déclenchée après validation transactionnelle du message.
- Vérification de la présence avant envoi afin de ne notifier que les destinataires hors ligne.
- Envoi VAPID avec `pywebpush`.
- Désactivation des abonnements répondant HTTP 404 ou 410.

### Endpoints livrés

- `POST /api/auth/register/`
- `POST /api/auth/verify-otp/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/contacts/sync/`
- `GET /api/conversations/`
- `POST /api/conversations/`
- `GET /api/conversations/{id}/messages/`
- `POST /api/conversations/{id}/messages/`
- `POST /api/media/presign/`
- `POST /api/media/{id}/complete/`
- `POST /api/notifications/subscriptions/`
- `GET /api/health/`
- `WS /ws/conversations/{id}/`

### Migrations et seed

- Onze fichiers de migrations initiales ont été générés pour les six apps.
- Certaines apps utilisent `0001_initial` puis `0002_initial` parce que Django sépare les clés étrangères vers le modèle utilisateur personnalisé afin de résoudre les cycles de dépendances.
- Le seed précédent a été remplacé par la commande idempotente `python manage.py seed_kozons`.
- Le seed crée 4 utilisateurs, 4 contacts, 3 conversations, 8 appartenances, 5 messages variés et 9 accusés.
- Une deuxième exécution du seed ne crée aucun doublon.

### Tests créés

- Inscription par téléphone, hachage du mot de passe, validation OTP et connexion JWT.
- Refus d’une inscription sans téléphone ni email.
- Synchronisation du carnet, détection d’un inscrit, création unidirectionnelle et exclusion de soi-même.
- Envoi de message idempotent, création de l’accusé et passage à l’état lu.
- Connexion WebSocket authentifiée, contrôle de présence et diffusion d’un nouveau message.

### Difficultés rencontrées et solutions

1. L’audit initial combiné a dépassé son délai pendant l’interrogation de `pip`. Les contrôles du système, des paquets et des outils ont été séparés.
2. La première installation des dépendances avait un délai trop court et a été interrompue. Une seconde installation a été lancée avec un délai de 120 secondes ; son processus a continué en arrière-plan et les paquets ont finalement été installés. Gunicorn, ajouté ensuite au fichier des dépendances, a été installé séparément.
3. Aucun serveur PostgreSQL, Redis, Docker ou FFmpeg n’est disponible localement. Des réglages de test sans service externe et une stack Docker complète ont été fournis.
4. Le premier test du seed attendait par erreur 8 accusés. Le décompte correct est 9 : deux pour la première conversation, un pour la seconde et six pour les deux messages du groupe. L’assertion a été corrigée, sans modification du seed.
5. Le premier modèle de message utilisait un `URLField`, incompatible avec les références persistantes `s3://`. Il a été remplacé par un `CharField` et la migration initiale a été ajustée avant livraison.
6. Accepter directement une URL média aurait permis l’injection d’une référence arbitraire. L’API accepte maintenant un identifiant de média et vérifie que l’objet est prêt, du bon type et rattaché à la conversation.
7. Un avertissement JWT indiquait que la clé de développement était inférieure à 32 octets. La valeur locale a été allongée et les réglages de production refusent toujours cette valeur par défaut.
8. Le contrôle global du graphe SQL PostgreSQL hors connexion a dépassé 120 secondes. Les processus résiduels avaient fini avant la tentative d’arrêt. Le contrôle a été remplacé par une génération ciblée du DDL PostgreSQL directement depuis les neuf modèles métier, terminée en environ onze secondes.
9. Daphne émet deux avertissements de dépréciation liés à la politique de boucle événementielle de Python 3.14 sous Windows. Ils proviennent de la dépendance, pas du code Kozons. L’image Docker utilise Python 3.13, version évitant ce problème actuel.
10. La commande Docker réelle ne pouvait pas être testée car Docker est absent. La syntaxe YAML et la présence des services obligatoires ont été vérifiées avec un parseur YAML.

### Vérifications finales effectuées

- `python manage.py check` : aucun problème.
- `python manage.py makemigrations --check --dry-run` : aucune migration manquante.
- `pytest` : 5 tests réussis.
- Migration complète sur SQLite isolé : réussie.
- Seed exécuté deux fois : idempotence confirmée.
- Comptage final du seed : 4 utilisateurs, 4 contacts, 3 conversations, 8 appartenances, 5 messages et 9 accusés.
- Contrôle `check --deploy` avec les réglages de production : aucun problème.
- Analyse de `docker-compose.yml` : YAML valide et services PostgreSQL, Redis, MinIO, HTTP, temps réel et worker présents.
- Génération ciblée du DDL avec le backend PostgreSQL Django : 57 instructions, avec tables et index principaux confirmés.
- Nettoyage de `.pytest_cache` et suppression de l’ancienne arborescence `messagerie` devenue vide.

### Limites de validation restantes

- L’exécution réelle sur PostgreSQL doit être vérifiée dans un environnement disposant du serveur.
- Les flux Redis réseau et Celery distribué doivent être testés avec les conteneurs ou l’infrastructure cible.
- Le traitement FFmpeg doit être testé avec des fichiers réels et différents codecs.
- Les intégrations MinIO/S3, Twilio, Africa’s Talking et VAPID nécessitent des identifiants réels ou de bac à sable.
- Un test de charge reste nécessaire pour dimensionner les workers, la capacité Channels, les pools PostgreSQL et les limites d’upload.

### Résultat

Le backend Kozons demandé est implémenté, documenté, migrable et couvert par les tests unitaires essentiels. La configuration de production refuse les secrets par défaut, tandis que la configuration de test permet de valider le métier sans services externes. Les validations d’intégration restantes dépendent uniquement des infrastructures et identifiants qui ne sont pas présents dans l’environnement local.

---

<a id="frontend"></a>

## 11 septembre 2026 — Construction du frontend PWA Next.js

### Objectif

Construire le frontend complet de Kozons sous la forme d’une PWA Next.js 15, avec une expérience de messagerie inspirée des conventions de Telegram sans reprendre sa marque, un layout mobile en pile, un layout desktop en trois colonnes, une couche REST découplée, du temps réel, les médias, les contacts, les groupes, le profil, les thèmes clair/sombre et un fonctionnement hors ligne minimal.

### Audit et organisation retenue

- Le backend Django existant a été préservé à la racine et le frontend isolé dans `frontend/`.
- Le dossier racine n’était pas un dépôt Git. Un dépôt Git limité à `frontend/` a été initialisé uniquement pour l’hébergement privé Sites.
- Les compétences Sites et Computer Use ont été suivies, car la tâche portait sur la création d’un site et exigeait des tests responsive réels.

### Fondation Next.js, TypeScript et Tailwind

- Création de `package.json` et `package-lock.json` avec Next.js 15.5.2, React 19, TypeScript strict, Tailwind CSS, React Query, Zustand, Socket.IO Client, `date-fns` et `next-pwa`.
- Création des configurations TypeScript, PostCSS, Tailwind, PWA et export statique.
- Création des providers React Query et thème, des styles globaux et de `.env.example`.
- Création d’un serveur statique Node sans dépendance supplémentaire pour rendre `npm start` compatible avec `output: "export"`.
- Centralisation des tokens clair/sombre, bulles, états, focus et animations réduites dans `app/globals.css`.
- Conservation du zoom navigateur pour l’accessibilité.

### Identité visuelle et PWA

- Logo Kozons original avec bulle et « K », sans reprise du logo Telegram.
- Icônes standard et maskable en SVG.
- Manifest complet : nom, description, français, couleurs, standalone, orientation, catégories, raccourcis et icônes.
- Service worker `next-pwa`, fallback `offline.html`, cache `NetworkFirst` pour conversations/messages et `StaleWhileRevalidate` pour les assets.
- Persistance Zustand des données chargées pour le mode hors ligne minimal.
- Invitation aux notifications seulement après une première conversation, si VAPID est configuré, puis demande de permission uniquement après un clic explicite.

### Écrans et composants livrés

- Connexion par téléphone/email, inscription avec choix du canal et vérification OTP en six champs avec compte à rebours et renvoi.
- Contacts inscrits, recherche, synchronisation, état vide, partage et démarrage d’une conversation.
- Création de groupe avec sélection multiple, nom et photo.
- Liste des conversations avec avatar, présence, aperçu, heure, non-lus et accusés.
- Navigation mobile en pile, bouton retour, FAB et navigation Discussions/Contacts/Profil.
- Layout desktop : colonne gauche fixe de 380 px, conversation flexible et panneau repliable de 340 px.
- Bulles, coches envoyé/reçu/lu accessibles, indicateur de saisie et envoi optimiste avec `client_id` UUID.
- Compositeur avec texte, emoji, pièces jointes et micro ; maintien pour enregistrer, relâchement pour envoyer, glissement de 80 px pour annuler.
- Lecteur vocal avec forme d’onde et progression.
- Visionneuse média plein écran avec précédent/suivant, Échap et zoom.
- Panneau de groupe avec membres, rôles, médias et sortie du groupe.
- Profil avec nom, statut, thème et photo ; le profil de démonstration est clairement en lecture seule.

### Architecture réseau et état

- `lib/api/client.ts` centralise `fetch`, le bearer token et une tentative unique de refresh JWT.
- `lib/api/hooks.ts` expose tous les appels via React Query ; aucun composant UI n’appelle directement l’API.
- Zustand est séparé en stores d’authentification, préférences et chat.
- Un adaptateur commun propose Socket.IO Client conformément à la stack et un transport WebSocket Channels compatible avec le backend existant.
- `NEXT_PUBLIC_REALTIME_TRANSPORT` sélectionne le protocole sans modifier l’UI.
- Une connexion est ouverte par conversation active ; messages, accusés, présence et saisie sont normalisés.

### Surface WebMCP

Deux outils page-scoped ont été ajoutés avec détection de fonctionnalité : `read_conversations` en lecture seule et `send_text_message`, qui réutilise exactement l’action de l’interface. Les schémas, validations, annotations et le nettoyage par `AbortSignal` sont présents. Aucun contexte WebMCP natif permettant leur exécution n’était disponible ; cette surface n’est donc pas annoncée comme validée en conditions réelles. WebMCP n’était pas une exigence utilisateur et cette limite n’est pas bloquante.

### Ajustements backend pour l’intégration frontend

- Champ `statut_personnalise` et migration `users/migrations/0002_user_statut_personnalise.py`.
- `POST /api/auth/resend-otp/`, `GET/PATCH /api/profile/`, `DELETE /api/conversations/{id}/leave/` et `GET /api/media/{id}/`.
- Promotion d’un nouvel administrateur lorsqu’un admin quitte un groupe.
- Support de `avatar_media_id` pour profil et groupe, avec validation du propriétaire, du type image et de l’état prêt.
- Conservation des références `s3://` durables et génération d’URL GET pré-signées courtes dans les sérialiseurs et événements temps réel.

Cette solution évite de persister une URL pré-signée expirante et bloque l’injection d’une référence arbitraire.

### Difficultés et solutions

1. Les premières installations npm et une première compilation ont dépassé leurs délais ; la présence des paquets a été contrôlée et les commandes relancées avec un délai adapté.
2. Une faute initiale dans le store d’authentification empêchait `setSession` d’appeler Zustand `set` ; elle a été corrigée avant validation.
3. Channels et Socket.IO utilisent des protocoles différents ; un transport interchangeable résout cette incompatibilité.
4. Les boutons de photo profil/groupe étaient d’abord seulement visuels ; ils ont été reliés aux inputs accessibles, aperçus, presigns S3 et identifiants média vérifiés.
5. `manage.py check` en profil dev attendait PostgreSQL absent ; il a été interrompu sans perte puis relancé avec les réglages de test SQLite.
6. Le pont natif Computer Use était indisponible (`native pipe unavailable`). Un smoke test Edge DevTools reproductible, sans dépendance, a servi de solution de repli.
7. Les premières captures arrivaient avant l’hydratation ; le test attend désormais un état visible stable.
8. Le premier rendu hydraté a détecté qu’un `useEffect` renvoyait implicitement `scrollIntoView` ; l’effet a été corrigé pour ne rien retourner.
9. Edge en ligne de commande imposait une largeur CSS minimale supérieure à 375 px ; l’émulation DevTools force maintenant le viewport exact.
10. Le widget Next.js produisait un faux positif d’erreur ; le test inspecte le shadow DOM et ne retient que les vraies erreurs runtime.
11. Le premier packaging Sites a interprété `C:` comme un hôte distant `tar` ; aucun fichier n’a été créé et la relance avec les chemins `/c/...` a réussi.
12. `open_in_codex` n’était pas exposé ; la publication a tout de même atteint `succeeded` et l’URL est consignée ci-dessous.
13. Les avertissements Git CRLF signalent uniquement la convention Windows de fins de ligne.

### Vérifications exécutées

- `npm run typecheck` : réussi.
- `npm run build` : réussi ; 11 pages statiques, service worker et fallback générés.
- `python manage.py check` avec les réglages de test : aucun problème.
- `python manage.py makemigrations --check --dry-run` : aucune migration manquante.
- `python -m pytest` : 5 tests réussis ; deux avertissements Daphne/Python 3.14 externes au code.
- `npm run test:responsive` : réussi à 375×812, 768×1024 et 1440×900.
- Largeur CSS exacte, aucun débordement horizontal, aucune erreur runtime et aucun écran bloqué pour les trois formats.
- Parcours mobile liste → conversation → retour et présence du compositeur vérifiés.
- Panneau d’informations desktop vérifié à 1440 px.
- Revue visuelle des captures mobile, tablette, desktop et troisième colonne.
- `npm start` testé : HTTP 200 pour `/`, `/auth/login`, `/chat`, `/manifest.json`, `/sw.js` et `/offline.html`, avec types MIME corrects.
- Archive d’hébergement vérifiée avec `dist/index.html`, `dist/.openai/hosting.json` et `dist/sw.js`.
- Dépôt frontend propre après commit de l’état validé.

### Publication privée

Version 1 publiée en accès privé propriétaire :

`https://kozons-chat-pwa-2026.hearty-cabin-4141.chatgpt.site`

Seul l’export statique du frontend a été publié. Le backend, PostgreSQL, Redis, Celery, S3 et les secrets ne le sont pas. Sans backend public configuré, les opérations distantes ne fonctionnent naturellement pas sur cette URL ; le mode démonstration reste disponible localement avec `NEXT_PUBLIC_DEMO_MODE=true`.

### Limites avant production réelle

- Configurer des origines API et WebSocket HTTPS/WSS ainsi que CORS et le proxy inverse.
- Tester installation PWA, mises à jour du service worker, MediaRecorder et gestes tactiles sur appareils physiques iOS/Android.
- Tester S3, FFmpeg, plusieurs codecs, VAPID et les notifications avec de vrais services.
- Compléter l’audit manuel par lecteurs d’écran.
- Le transport Socket.IO nécessite une passerelle serveur compatible ; le backend livré utilise immédiatement le transport Channels.
- Les validations PostgreSQL, Redis, S3, Celery et Web Push réelles restent dépendantes de l’infrastructure externe.

### Résultat

Le frontend Kozons est implémenté, compilable, responsive, installable comme PWA, documenté, relié aux contrats REST/temps réel, doté d’un mode démonstration et publié en privé. Les composants restent découplés du réseau et les adaptations backend nécessaires sont incluses avec leur migration.

---

<a id="lancement"></a>

## 11 septembre 2026 — Lancement local du frontend

### Demande

Lancer l’application Kozons afin qu’elle soit immédiatement consultable.

### Actions réalisées

- Vérification que le port local 3000 était disponible.
- Démarrage de Next.js en tâche de fond et fenêtre masquée depuis `frontend/`.
- Activation du mode démonstration avec `NEXT_PUBLIC_DEMO_MODE=true`.
- Sélection du transport Django Channels pour conserver la compatibilité avec le backend livré.
- Requête de contrôle vers `http://127.0.0.1:3000/chat`.

### Vérification

- Next.js 15.5.2 a démarré correctement.
- La route `/chat` a été compilée.
- Le serveur a retourné HTTP 200.
- Le processus reste actif sur le port 3000 après la vérification.

### Difficulté rencontrée

La compétence Computer Use a été initialisée pour ouvrir automatiquement Microsoft Edge, mais son pont natif Windows est toujours indisponible avec l’erreur `native pipe unavailable`.

### Solution

Le serveur a été laissé actif et l’URL locale est fournie directement à l’utilisateur. Aucun contournement par automatisation PowerShell de l’interface Windows n’a été employé.

---

<a id="securite"></a>

## 12 septembre 2026 — Audit et durcissement de sécurité applicative

### Demande

Auditer et renforcer Kozons sur l’authentification, les OTP, les WebSockets, la confidentialité des contacts, les médias, le transport, les abus, la validation des entrées et les secrets. Produire les réglages/middlewares Django, la configuration DRF/Channels et une checklist justifiée.

### Audit initial

Les protections déjà présentes ont d’abord été inventoriées : OTP haché valable cinq minutes, compteur d’essais, JWT courts avec rotation/blacklist, contrôle d’appartenance lors de l’ouverture WebSocket, listes MIME/taille, références S3 opaques, pagination par curseur et appels FFmpeg sans shell.

Les écarts constatés étaient : PBKDF2 par défaut au lieu d’Argon2, absence de dépendance CORS et de throttling DRF, secret de développement par défaut, refresh JWT exposé au JavaScript et persisté en `localStorage`, absence de logout/révocation globale, limites OTP seulement par identifiant, réponses contacts/membres exposant téléphone/email, contrôle WebSocket uniquement à la connexion, token WebSocket dans l’URL, absence de contrôle de signature/antivirus média, absence de CSP et de journal d’audit structuré.

### Références techniques vérifiées

Les choix ont été confrontés aux documentations officielles Django (Argon2 et validateurs), Django REST Framework (throttling), SimpleJWT (rotation et blacklist), Channels (validation d’origine), `django-cors-headers`, ainsi qu’aux recommandations OWASP sur upload, validation, XSS, CSP et en-têtes HTTP. Les limites documentées des throttles DRF non atomiques ont conduit à conserver une seconde couche métier Redis pour les opérations critiques.

### Actions réalisées

1. Ajout de `argon2-cffi` et `django-cors-headers` aux dépendances. Argon2 est le premier hasher ; PBKDF2 reste lisible pour une migration progressive. La longueur minimale passe à 10 caractères, avec contrôles des mots de passe courants, numériques et trop proches des attributs utilisateur.
2. L’access JWT passe à 10 minutes. Le refresh tourne à chaque usage, l’ancien est blacklisté et le refresh n’est plus retourné au JavaScript : il est posé dans un cookie `HttpOnly`, `Secure` en production et `SameSite=Strict`.
3. Ajout de `/logout/`, `/logout-all/` et `/change-password/`. Une version de jeton (`ver`) permet de révoquer instantanément tous les access/refresh déjà émis, sans course liée à la précision à la seconde du claim `iat`. Celery Beat purge quotidiennement les tokens expirés.
4. Ajout d’une comparaison de mot de passe factice lorsqu’un identifiant de connexion n’existe pas afin de réduire l’oracle temporel d’énumération de comptes.
5. Ajout de compteurs HMAC Redis par identifiant **et** IP pour inscription, login, vérification et renvoi OTP. Des compteurs par utilisateur couvrent aussi les messages REST/WebSocket et les uploads.
6. Correction du compteur OTP : l’incrément d’un essai invalide est maintenant validé en base avant de lever l’erreur, afin qu’un rollback transactionnel ne rende pas les essais illimités.
7. Ajout des throttles DRF global burst/sustained et des scopes inscription, login, OTP, contacts, messages, upload et session. `DRF_NUM_PROXIES` pilote la lecture prudente de l’IP transmise par proxy.
8. Ajout du `PublicUserSerializer`; téléphone et email ne sont plus exposés pour les contacts synchronisés ni pour les membres de conversation.
9. Étude de la synchronisation privée des contacts documentée : rejet d’un SHA-256 client naïf, vulnérable au dictionnaire/corrélation ; recommandation d’un PSI/OPRF audité ou d’une recherche k-anonyme avant passage à très grande échelle.
10. WebSocket renforcé avec JWT révocable, `OriginValidator`, token navigateur dans un sous-protocole plutôt que l’URL, query token interdite en production et contrôle d’appartenance avant chaque événement entrant et sortant. Une révocation de membre entraîne une fermeture 4403.
11. Ajout d’une validation texte Unicode NFC, longueur maximale et rejet des caractères de contrôle. Le texte reste rendu par React comme nœud texte, sans `dangerouslySetInnerHTML`, ce qui assure l’encodage contextuel anti-XSS.
12. Médias renforcés : taille/MIME au presign, contrôle `HeadObject`, signature binaire réelle, analyse ClamAV en flux avant toute publication, traitement FFmpeg seulement ensuite, suppression d’un objet invalide/infecté. Les réponses de suivi n’exposent plus les références internes `s3://`, seulement des URL GET valables 300 secondes.
13. Ajout d’un service ClamAV dans Compose et d’une configuration fail-closed en production. Redis reçoit une authentification ; PostgreSQL, Redis, MinIO et l’application tirent leurs identifiants/secrets des variables d’environnement.
14. Ajout de CORS explicite, CSP, `nosniff`, anti-framing, referrer policy, permissions policy, cookies sûrs, redirection HTTPS et HSTS production. `prod.py` refuse les origines non HTTPS, les secrets faibles/absents, les OTP fixes et le fournisseur SMS console.
15. Ajout du modèle `SecurityAuditEvent` et de sa migration. Inscription, OTP, login, logout, révocation globale, changement de mot de passe et profil sont journalisés avec IP/identifiant HMACés, sans OTP, mot de passe ni JWT.
16. Frontend : access JWT gardé seulement en mémoire, bootstrap de session via le refresh cookie, purge du store/caches privés au logout, suppression du cache Workbox des réponses API authentifiées, origine API/WS relative par défaut pour éviter le mixed content, headers du serveur statique et sous-protocole Channels sécurisé.
17. Création de `SECURITY.md` : paramètres/middlewares, throttles, architecture Channels, étude contacts, chaîne média, stratégie XSS, journal d’audit, checklist fait/à faire et procédure avant production.
18. Mise à jour de `.env.example`, `README.md`, `frontend/README.md`, du Compose, des types frontend et des contrats d’authentification.

### Difficultés rencontrées et solutions

1. Un premier lot de patchs n’avait pas été appliqué. Chaque fichier a été contrôlé avec recherche ciblée, puis les changements ont été réappliqués en blocs plus petits et vérifiés immédiatement.
2. DRF n’accepte pas une syntaxe de taux `30/15min` : son parseur utilise seulement la première lettre de seconde/minute/heure/jour. Les scopes ont donc été exprimés en taux natifs horaires, et les fenêtres exactes de 15 minutes restent assurées par les compteurs Redis métier.
3. Le test OTP a révélé que lever une exception dans `transaction.atomic` annulait aussi la sauvegarde du nombre d’essais. La fonction a été restructurée pour quitter proprement la transaction avant de lever l’erreur.
4. Une invalidation fondée uniquement sur `iat` présente une ambiguïté si un nouveau jeton est émis dans la même seconde. Un compteur de version signé dans chaque token résout l’ambiguïté et révoque immédiatement les anciennes versions.
5. Le cache PWA `NetworkFirst` des API utilisait l’URL comme clé, pas l’utilisateur : sur un navigateur partagé, un second compte pouvait recevoir le cache du premier. Les caches API Workbox ont été supprimés ; le cache Zustand hors ligne est vidé explicitement au logout.
6. Le simple hash client des numéros donne une fausse impression de confidentialité à cause de l’espace de recherche réduit. La solution choisie est de documenter un protocole privé robuste comme évolution, tout en minimisant les données dans la version actuelle.
7. Docker n’est pas installé sur ce poste, donc `docker compose config` et le démarrage réel ClamAV n’ont pas pu être exécutés. Le YAML a été chargé avec PyYAML pour valider sa structure ; l’intégration ClamAV reste signalée « à valider en infrastructure ».
8. Le contrôle Django production a d’abord émis `security.W009` parce que la valeur de test utilisée dans la commande était trop courte. Le seuil `DJANGO_SECRET_KEY` production a été aligné à 50 caractères minimum et le contrôle a été relancé avec une valeur aléatoire longue.
9. Le build PWA prend environ 100 secondes sur ce poste ; il a été laissé terminer, avec des mises à jour intermédiaires plutôt que d’être interrompu.

### Tests ajoutés

- hash Argon2 et vérification de mot de passe ;
- refresh par cookie HttpOnly, logout/blacklist et révocation globale d’un access existant ;
- persistance d’un essai OTP invalide ;
- absence de téléphone/email dans une réponse de synchronisation ;
- présence des en-têtes de sécurité ;
- revalidation d’appartenance WebSocket après retrait du membre ;
- rejet des caractères de contrôle et inertie d’une chaîne ressemblant à du HTML ;
- validation de signature PNG et rejet d’un faux fichier.

### Éléments restant à faire avant production

- Déployer et tester réellement le proxy TLS, HSTS/preload, WAF/DDoS, Redis/S3 privés et le service ClamAV, notamment avec EICAR et sous charge.
- Concevoir/faire auditer PSI/OPRF ou une alternative k-anonyme pour la découverte privée des contacts.
- Ajouter les événements d’audit au futur workflow de suppression de compte, qui n’existe pas encore.
- Définir rétention, accès et export SIEM du journal d’audit et réaliser un test de pénétration externe.

### Vérifications finales

- Installation des dépendances Python : réussie (`django-cors-headers 4.9.0`, Argon2 déjà présent).
- `python manage.py check --settings=kozons.settings.test` : aucun problème.
- `python manage.py makemigrations --check --dry-run --settings=kozons.settings.test` : aucune migration manquante.
- `python -m pytest` : 12 tests réussis ; deux avertissements de dépréciation Daphne liés à Python 3.14, sans échec applicatif.
- `npm run typecheck` : réussi.
- `npm run build` : réussi, 11 pages statiques et service worker générés.
- `python manage.py check --deploy --settings=kozons.settings.prod` avec variables de validation : aucun problème.
- YAML Compose chargé avec succès par PyYAML ; validation Docker réelle indisponible sur ce poste.
- Le build avait laissé l’ancien processus Next à l’écoute mais sans réponse. Ce processus précis a été arrêté, le serveur de développement a été relancé en fenêtre masquée avec le mode démonstration et le transport Channels, puis `/chat` a de nouveau répondu HTTP 200 sur le port 3000.

---

<a id="logo-donnees"></a>

## 12 septembre 2026 — Nouveau logo, retrait des données fictives et accueil sur la connexion

### Demande

Intégrer le logo fourni `Gemini_Generated_Image_n9dc6wn9dc6wn9dc.jfif`, supprimer les données de test visibles et faire arriver toute première visite sur la page de connexion, avec possibilité de créer un compte.

### Analyse initiale

- La racine `/` redirigeait systématiquement vers `/chat`.
- `/chat` autorisait un mode `NEXT_PUBLIC_DEMO_MODE` qui injectait un utilisateur Amina, quatre contacts, trois conversations et six messages fictifs.
- Contacts et création de groupe réinjectaient également ces données au montage.
- Profil, envoi de messages et shell de chat utilisaient un utilisateur fictif comme valeur de repli.
- Le lien « Créer un compte » existait déjà sur la connexion, mais le parcours initial le contournait.
- Le logo affiché était un carré en dégradé contenant seulement la lettre K ; le manifeste PWA utilisait encore deux anciens SVG.

### Actions réalisées

1. Inspection visuelle du logo original : symbole K bleu/turquoise avec avion en papier, bulle de discussion et mot Kozons sur fond blanc.
2. Copie non destructive de l’original dans `frontend/public/branding/kozons-logo.jfif`.
3. Utilisation de la compétence ImageGen en mode intégré pour produire `frontend/public/branding/kozons-app-icon.png`, une déclinaison carrée du symbole destinée à l’icône PWA et aux en-têtes compacts.
4. Prompt final utilisé pour l’icône : « créer une icône carrée 1024×1024 utilisant seulement le symbole K/avion/bulle existant, retirer le mot Kozons, centrer et agrandir avec marge équilibrée sur fond blanc, préserver géométrie, couleurs, épaisseur et trois points, sans ajout, texte, ombre, dégradé ni watermark ».
5. Le composant `Brand` utilise maintenant l’icône carrée dans les en-têtes et une fenêtre de cadrage de l’image originale complète sur les écrans d’authentification.
6. Mise à jour des métadonnées Next.js, de l’icône Apple et du manifeste PWA. L’ancienne paire d’icônes SVG non utilisée a été supprimée.
7. Le `start_url` PWA est désormais `/auth/login`. La racine attend la restauration éventuelle du refresh cookie, puis redirige vers `/chat` si une session valide existe ou `/auth/login` sinon.
8. Création de `RequireAuth`, appliqué à Chat, Contacts, Nouveau groupe et Profil. Un accès direct à ces routes sans session retourne vers la connexion.
9. La page de connexion redirige automatiquement un utilisateur déjà authentifié vers ses discussions. Le lien « Créer un compte » reste clairement visible et pointe vers `/auth/register`.
10. Mise en cohérence du formulaire d’inscription avec la politique backend : 10 caractères minimum et remplacement du nom fictif en placeholder par « Votre nom ».
11. Suppression de `frontend/lib/demo-data.ts` et de toutes les branches `bootstrapDemo`, `demoUser`, `NEXT_PUBLIC_DEMO_MODE` et des comportements de profil/message sans compte réel.
12. Incrément de version du store Zustand avec migration vidant conversations, messages, contacts et conversation active : les anciennes données fictives déjà stockées dans un navigateur ne sont pas réhydratées.
13. Retrait de la variable de démonstration dans `.env.example` et mise à jour de `frontend/README.md` pour indiquer que l’application nécessite désormais le backend réel.
14. Création de la configuration locale ignorée `.env.local` reliant le frontend à l’API `localhost:8000` et à Channels `localhost:8001`, sans mode démonstration ni secret.
15. Adaptation du smoke test responsive : il vérifie maintenant redirection vers `/auth/login`, formulaire, lien d’inscription, logo chargé, absence des anciens noms fictifs, absence d’erreur runtime et absence de débordement.

### Portée de la suppression

Les données fictives embarquées dans l’interface et leur cache navigateur ont été supprimés. Les tests automatisés backend n’ont pas été supprimés : ils créent leurs données dans une base SQLite en mémoire isolée et restent nécessaires pour prévenir les régressions. Le script de seed backend demandé dans les livrables précédents reste une commande manuelle de développement et n’est jamais exécuté au démarrage.

Une vérification des ports 5432 et 6379 a montré qu’aucun PostgreSQL ni Redis local n’était actif. Il n’existait donc aucune base locale en cours contenant des comptes de seed à purger sans risquer de supprimer des données réelles.

### Difficultés et solutions

1. La déclinaison carrée devait rester lisible comme icône PWA sans écraser l’image rectangulaire. Une variante dédiée a été créée à partir du logo fourni, tandis que l’original est conservé pour l’authentification.
2. Le premier cadrage CSS de l’original rognait le bas puis la dernière lettre du mot Kozons. Deux contrôles par capture à 375 px ont permis d’augmenter successivement la hauteur et la largeur de la fenêtre jusqu’à afficher le logo entier.
3. Le navigateur Edge puis le navigateur intégré n’étaient pas disponibles via Computer Use (`Browser is not available`). Le smoke test Edge/DevTools déjà présent dans le projet a servi de solution de repli reproductible, et les captures ont été inspectées avec l’outil d’image local.
4. Un build Next exécuté pendant le serveur de développement peut rendre le processus existant incohérent à cause du dossier `.next` partagé. Le processus exact à l’écoute a été arrêté avant chaque build, puis le serveur a été relancé et contrôlé en HTTP.
5. Le premier redémarrage avec plusieurs variables d’environnement dans une seule commande a été bloqué par la politique d’exécution. Le serveur a été relancé avec la configuration minimale sûre ; l’application utilise son origine courante tant qu’un backend distinct n’est pas configuré.

### Vérifications

- Recherche globale : aucune référence applicative à `demoUser`, `bootstrapDemo`, `NEXT_PUBLIC_DEMO_MODE`, aux conversations ou aux messages fictifs.
- `npm run typecheck` : réussi.
- `npm run build` : réussi ; 11 pages statiques et service worker générés.
- `npm run test:responsive` sur `/` : réussi à 375×812, 768×1024 et 1440×900.
- Même test avec entrée directe `/chat` : redirection correcte vers `/auth/login` aux trois largeurs.
- Pour chaque viewport : formulaire de connexion présent, lien `/auth/register` présent, logo chargé, aucune donnée fictive, aucune erreur runtime et aucun débordement horizontal.
- Inspection visuelle finale de `login-375.png` : logo Kozons complet, formulaire lisible et lien « Créer un compte » visible.
- `/auth/register` retourne HTTP 200 et contient « Créer votre compte ».
- Serveur Next relancé sans mode démonstration ; `/` retourne HTTP 200 sur le port 3000.

---

<a id="failed-to-fetch"></a>

## 12 septembre 2026 — Correction de l’erreur « Failed to fetch » à l’inscription

### Signalement

L’utilisateur obtenait `Failed to fetch` après validation du formulaire de création de compte.

### Diagnostic

- Frontend : port 3000 actif.
- Configuration frontend : API attendue sur `127.0.0.1:8000`, WebSocket sur `127.0.0.1:8001`.
- API, WebSocket, PostgreSQL et Redis : aucun processus à l’écoute.
- La requête échouait donc au niveau réseau avant toute réponse HTTP ; ce n’était ni une erreur de validation du formulaire ni une erreur CORS applicative.

### Solution implémentée

1. Ajout de `kozons.settings.local`, profil local autonome sans seed : SQLite persistante locale, cache et channel layer en mémoire, Celery synchrone, stockage média simulé et cookies non sécurisés uniquement sur localhost.
2. PostgreSQL reste la base principale des profils dev/prod ; SQLite sert uniquement à rendre le développement possible sur ce poste dépourvu de Docker/PostgreSQL/Redis.
3. Ajout de `kozons-local.sqlite3` au `.gitignore` afin qu’aucune donnée locale ne soit versionnée.
4. Alignement des URLs frontend sur `127.0.0.1` pour éviter un mélange `localhost`/`127.0.0.1` incompatible avec le cookie refresh `SameSite=Strict`.
5. Exécution de toutes les migrations dans une base locale initialement vide.
6. Démarrage de l’API Django sur `127.0.0.1:8000` et de Daphne/Channels sur `127.0.0.1:8001`, en plus du frontend sur 3000.
7. Activation locale seulement de `OTP_FIXED_CODE=000000` pour terminer l’inscription sans fournisseur SMS. Le profil production refuse toujours un OTP fixe.
8. Ajout d’une traduction des erreurs réseau dans le client REST : si l’API redevient indisponible, l’interface affiche désormais « Impossible de joindre le serveur Kozons. Vérifiez qu’il est démarré. » au lieu du message technique anglais `Failed to fetch`.
9. Documentation du profil local dans `README.md`.

### Vérification fonctionnelle

- `/api/health/` : HTTP 200.
- Préflight CORS de `http://127.0.0.1:3000` vers `/api/auth/register/` : HTTP 200, origine et credentials autorisés.
- Inscription invalide `{}` : HTTP 400 JSON, prouvant que le frontend peut désormais joindre l’API.
- Parcours technique complet : inscription HTTP 201, OTP HTTP 200, connexion HTTP 200 avec access JWT.
- Le compte technique, son OTP et ses événements d’audit ont été supprimés immédiatement après le contrôle.
- État final de la base locale : 0 utilisateur, 0 OTP, 0 événement d’audit ; aucune donnée de test conservée.
- `python manage.py check` avec le profil local : aucun problème.
- `npm run typecheck` : réussi.
- Services finaux à l’écoute : frontend 3000, API 8000, WebSocket 8001.

### Difficultés et solutions

1. Le premier POST de contrôle contenait `Contrôle local`; PowerShell l’a envoyé avec un encodage incompatible et Django a correctement rejeté le JSON UTF-8. Le test réseau a été relancé avec une charge ASCII. Le navigateur, lui, encode normalement les JSON en UTF-8.
2. `daphne.exe` n’était pas exposé dans le PATH Windows. Le module installé a été lancé de manière portable avec `python -m daphne`.
3. Aucun moteur PostgreSQL/Redis ni Docker n’est disponible localement. Le profil SQLite vide évite de bloquer l’interface sans modifier les choix de production.
- Le journal de démarrage Next confirme le chargement de `.env.local`; le processus final écoute sur le port 3000 et la racine répond HTTP 200.

---

<a id="otp-local"></a>

## 12 septembre 2026 — Résolution de l’absence d’e-mail ou de SMS OTP

### Signalement

Après l’inscription, le compte restait inactif et l’utilisateur ne pouvait pas se connecter, car aucun e-mail ni SMS contenant le code de vérification n’était reçu.

### Cause identifiée

Le profil de développement local utilisait volontairement deux fournisseurs de simulation : le backend e-mail `console` de Django et `ConsoleSMSProvider`. Ils écrivent le code dans les journaux du serveur, mais ne contactent aucun service externe. La génération, le stockage haché et la vérification de l’OTP fonctionnaient ; seule la livraison réelle n’était pas configurée.

### Solutions implémentées

1. Ajout de `NEXT_PUBLIC_LOCAL_OTP_CODE=000000` dans la configuration frontend locale uniquement.
2. Ajout sur l’écran `/auth/verify` d’un avertissement explicite « Mode local » et d’un bouton « Utiliser le code 000000 » qui remplit les six cases. Le code de développement n’est ainsi plus caché dans les journaux techniques.
3. Ajout de toutes les options SMTP Django dans `kozons/settings/base.py` : hôte, port, TLS/SSL, utilisateur, mot de passe et délai de connexion.
4. Retrait du forçage du backend console dans `kozons.settings.local`, afin de permettre l’activation d’un serveur SMTP par variables d’environnement sans modifier le code.
5. Ajout dans `.env.example` d’un exemple SMTP Gmail utilisant le port 587 et TLS. Les identifiants restent des placeholders et aucun secret réel n’a été ajouté au dépôt.
6. Ajout d’une protection de production : `kozons.settings.prod` refuse désormais de démarrer avec le backend e-mail console, tout comme il refusait déjà l’OTP fixe et le fournisseur SMS console.
7. Documentation des deux parcours dans `README.md` : code local immédiat, ou livraison réelle par SMTP/Twilio/Africa’s Talking après configuration privée des identifiants.
8. Ajout d’un test automatisé vérifiant qu’une inscription par e-mail produit bien un message à la bonne adresse et contenant l’OTP attendu avec le backend e-mail de test.
9. Ajout sur la connexion du lien « Compte non vérifié ? Recevoir un nouveau code ». L’identifiant déjà saisi est transmis à l’écran OTP.
10. Si la session navigateur a été fermée et que l’identifiant n’est plus mémorisé, `/auth/verify` propose désormais de saisir l’e-mail ou le téléphone puis demande un nouvel OTP. L’utilisateur peut donc reprendre une inscription interrompue sans créer un second compte.
11. Les erreurs de renvoi OTP sont maintenant affichées dans l’interface au lieu de produire une promesse rejetée non gérée.
12. Le bouton OTP local demande d’abord un nouveau code au serveur avant de remplir `000000`. Il reste donc fonctionnel même si le code créé lors de l’inscription a dépassé sa validité de cinq minutes.
13. L’adresse personnelle signalée n’est jamais inscrite en dur dans l’interface : le formulaire de récupération utilise un exemple générique.

### Limite externe et règle de sécurité

L’envoi réel ne peut pas être activé sans identifiants d’un compte expéditeur SMTP ou d’un fournisseur SMS. Ces secrets appartiennent à l’utilisateur et ne doivent jamais être copiés dans le code, dans `rapport.md` ou dans une conversation. Pour Gmail, il faut utiliser un mot de passe d’application associé à un compte protégé par validation en deux étapes, jamais le mot de passe principal. En attendant cette configuration externe, le parcours local est utilisable avec `000000`.

### Difficulté rencontrée et solution

Il fallait rendre le développement utilisable sans affaiblir la production. L’OTP fixe est donc exposé uniquement par `.env.local`, fichier ignoré, tandis que l’exemple frontend laisse cette variable vide et que le profil Django de production interdit explicitement tout OTP fixe ou fournisseur de livraison factice.

Le premier test d’envoi a observé une boîte e-mail vide alors que l’inscription répondait HTTP 201. L’analyse a confirmé que l’envoi est correctement différé avec `transaction.on_commit`, afin de ne jamais envoyer un OTP si la création du compte est annulée. La transaction englobante de `pytest-django` n’avait simplement pas encore été validée. Le test a été corrigé avec l’exécution explicite des callbacks de commit ; aucune régression du code métier n’était présente.

### Vérifications finales

- Les journaux locaux confirment l’inscription réussie de l’adresse fournie, la génération de l’OTP `000000` et son impression par le backend console. Ils confirment donc précisément pourquoi aucun message n’est arrivé dans Gmail.
- La base locale contient un seul compte réel, celui inscrit par l’utilisateur. Il est conservé et reste inactif jusqu’à la validation OTP ; aucune donnée de seed ou de test n’a été ajoutée.
- Suite complète backend : 13 tests réussis.
- Test spécifique d’inscription e-mail : destinataire et contenu OTP vérifiés.
- `npm run typecheck` : réussi.
- Smoke test responsive : réussi à 375×812, 768×1024 et 1440×900, sans erreur runtime ni débordement ; le lien de récupération est visible aux trois largeurs.
- `python manage.py check` avec le profil local : aucun problème.
- Frontend, API et WebSocket restent disponibles respectivement sur les ports 3000, 8000 et 8001.

---

<a id="reseau-otp"></a>

## 12 septembre 2026 — Accès depuis un autre appareil et activation réelle des OTP

### Demande

Ajouter un sommaire au rapport, corriger le `TypeError` rencontré lors d’une inscription depuis un autre appareil et expliquer comment activer la livraison réelle des OTP par e-mail et SMS.

### Diagnostic réseau

- Le PC hôte possède actuellement l’adresse Wi-Fi privée `192.168.1.3`.
- Le frontend écoute sur toutes les interfaces au port 3000, mais l’API Django et Daphne écoutaient uniquement sur `127.0.0.1`.
- Les URLs publiques compilées dans le frontend pointaient aussi vers `127.0.0.1:8000` et `127.0.0.1:8001`.
- Sur un téléphone, `127.0.0.1` désigne le téléphone lui-même. La requête d’inscription ne pouvait donc jamais atteindre Django et se terminait par une erreur réseau JavaScript de type `TypeError`.

### Corrections implémentées

1. Ajout d’un sommaire navigable au début du présent rapport, avec un lien vers chaque intervention principale.
2. Création de `frontend/lib/network.ts`, qui résout les URLs de service côté navigateur.
3. Lorsqu’une URL configurée contient `localhost` ou `127.0.0.1` mais que Kozons est ouvert avec une adresse réseau, le frontend remplace automatiquement l’hôte de bouclage par l’hôte courant. Un téléphone ouvrant `192.168.1.3:3000` utilise donc automatiquement `192.168.1.3:8000` pour REST et `192.168.1.3:8001` pour Channels.
4. Application de cette résolution à tous les appels REST, au renouvellement JWT et aux connexions WebSocket.
5. Ajout de `KOZONS_LOCAL_NETWORK_ORIGINS` au profil Django local. Les hôtes, origines CORS, origines CSRF et origines WebSocket supplémentaires sont dérivés de cette liste et des interfaces IPv4 privées réellement présentes sur le PC ; aucune origine Internet arbitraire n’est autorisée.
6. Ajout d’une option `HOST` au serveur statique frontend afin qu’un export puisse être volontairement exposé au réseau local avec `HOST=0.0.0.0`.
7. Documentation des commandes réseau local, de l’adresse d’accès et de la contrainte de pare-feu Windows.
8. Suppression du forçage du fournisseur SMS console dans `kozons.settings.local`. Un fournisseur Twilio ou Africa’s Talking peut maintenant être activé localement uniquement par variables d’environnement.
9. Ajout de validations de démarrage en production : une configuration SMTP, Twilio ou Africa’s Talking sélectionnée mais incomplète provoque désormais une erreur explicite.
10. Ajout dans `README.md` des procédures détaillées d’activation Gmail SMTP, Twilio SMS et Africa’s Talking, avec rappel de retirer l’OTP fixe et le code public local.
11. Ajout de `kozons.asgi_local`, point d’entrée Channels local autonome qui charge explicitement `kozons.settings.local` sans dépendre d’une variable de shell oubliée.
12. Ajout de `KOZONS_USE_RANDOM_OTP=true` pour désactiver sans ambiguïté le code fixe du profil local lorsqu’un fournisseur réel est testé. Sans cette option, le développement continue d’utiliser `000000`.

### Difficultés et solutions

Une adresse Wi-Fi peut changer après une reconnexion ou un redémarrage du routeur. L’adresse n’est donc pas inscrite en dur dans le code applicatif : Django la reçoit par `KOZONS_LOCAL_NETWORK_ORIGINS`, tandis que le navigateur dérive dynamiquement l’adresse des API depuis l’URL utilisée pour ouvrir Kozons.

Le profil local détecte aussi automatiquement les adresses IPv4 privées du PC. Des secrets de développement clairement marqués comme non sûrs et l’OTP fixe `000000` y servent de valeurs de repli afin que les commandes de lancement ne contiennent pas de secrets factices. Le profil production reste séparé et refuse l’OTP fixe ainsi que les fournisseurs console.

L’accès réseau local reste volontairement limité aux interfaces privées détectées et aux éventuelles origines supplémentaires explicitement configurées, afin de conserver les protections CORS, CSRF et WebSocket. Si l’adresse IPv4 change, un redémarrage de Django/Daphne suffit normalement à la détecter ; `KOZONS_LOCAL_NETWORK_ORIGINS` permet de déclarer manuellement un cas particulier.

Le premier lancement de `kozons.asgi_local` a encore chargé `kozons.settings.dev` : l’import du paquet `kozons` initialise Celery avant le module ASGI, et Celery avait déjà défini cette valeur. L’entrée strictement locale utilise désormais une affectation explicite au lieu de `setdefault`; Daphne charge ainsi le bon profil sans affaiblir les entrées de production.

Le premier smoke test via l’adresse Wi-Fi a atteint la connexion sans erreur runtime, mais a signalé le logo comme absent alors que le fichier répondait HTTP 200. Le contrôle était exécuté dès l’apparition du texte, avant la fin du téléchargement de l’image sur ce chemin réseau. Le test attend maintenant `complete` et une largeur naturelle non nulle avant d’évaluer la page, ce qui distingue un chargement lent d’une image réellement cassée.

### Activation réelle des OTP

- E-mail : backend SMTP Django sur `smtp.gmail.com:587` avec TLS, adresse expéditrice et mot de passe d’application Google. La validation en deux étapes Google est nécessaire pour créer ce mot de passe.
- SMS : `TwilioSMSProvider` avec SID, jeton et numéro Twilio compatible SMS, ou `AfricasTalkingSMSProvider` avec identifiant et clé API.
- Production : retirer `OTP_FIXED_CODE` et `NEXT_PUBLIC_LOCAL_OTP_CODE`, utiliser Celery avec Redis et redémarrer tous les processus après ajout des secrets.
- Sécurité : aucun secret réel n’a été créé, demandé ou stocké pendant l’intervention. L’activation finale dépend de comptes fournisseurs appartenant à l’utilisateur.

### Vérifications finales

- API et Daphne relancés sur `0.0.0.0`, ports 8000 et 8001 ; frontend toujours disponible sur toutes les interfaces au port 3000.
- Préflight CORS depuis `http://192.168.1.3:3000` : HTTP 200, origine exacte et credentials autorisés.
- POST invalide vers `http://192.168.1.3:8000/api/auth/register/` : HTTP 400 JSON attendu. La requête traverse donc réellement le réseau local et atteint DRF, sans créer de donnée.
- Les journaux de l’API confirment que le navigateur du smoke test lancé sur l’adresse Wi-Fi a demandé `/api/auth/refresh/` via `192.168.1.3`, preuve que la résolution dynamique remplace bien `127.0.0.1`.
- Smoke test via `http://192.168.1.3:3000` réussi à 375×812, 768×1024 et 1440×900, sans erreur runtime ni débordement.
- Suite backend complète : 13 tests réussis.
- Tests d’authentification ciblés : 7 réussis.
- `python manage.py check --settings=kozons.settings.local` : aucun problème.
- `npm run typecheck` : réussi.

---

<a id="messagerie-avancee"></a>

## 12 septembre 2026 — Messagerie avancée, groupes, multi-appareils et notifications iOS

### Objectif

Ajouter la modification, les deux modes de suppression, le transfert, la recherche, les réactions emoji, les droits d’administration de groupe, la synchronisation multi-appareils et le parcours iOS préalable aux notifications, sans déplacer la logique métier dans les vues ou les composants visuels.

### Modèle et migrations

- `conversations/models.py` ajoute `envoi_messages`, contraint à `tous` ou `admins`.
- `messaging/models.py` ajoute `modifie_le`, `supprime_pour_tous_le` et `conversation_origine` au message.
- La nouvelle table `message_masque_utilisateur` stocke les suppressions « pour moi » avec unicité message/utilisateur.
- La nouvelle table `reaction_message` garantit une réaction active au maximum par utilisateur et message; son index `(message, emoji)` facilite les compteurs.
- Les migrations `conversations.0003` et `messaging.0003` créent ces structures.
- `messaging.0004` crée sous PostgreSQL, avec `CREATE INDEX CONCURRENTLY`, l’index GIN partiel `message_contenu_fts_idx` sur le vecteur français des messages texte non supprimés. SQLite ignore volontairement cette opération.
- `.env.example` documente `MESSAGE_DELETE_FOR_EVERYONE_HOURS=48`.

### Backend REST et services

- `messaging/services.py` assure la propriété du message avant modification/suppression, applique la fenêtre de 48 heures, crée les masquages personnels, transfère texte ou référence média vers une à vingt conversations et gère six réactions autorisées.
- La suppression globale est logique : les sérialisations et événements n’exposent plus le contenu, le média ou la durée, mais l’historique et les accusés restent cohérents.
- Le transfert copie la référence objet plutôt que le fichier et conserve la conversation d’origine.
- `messaging/selectors.py` exclut les messages masqués et utilise `SearchVector`, `SearchQuery` et `SearchRank` en français sur PostgreSQL, avec `icontains` pour SQLite.
- Sérialiseurs, vues et routes exposent `PATCH/DELETE /api/messages/{id}/`, `POST /api/messages/{id}/forward/`, `POST/DELETE /api/messages/{id}/reaction/` et `GET /api/conversations/{id}/messages/search/`.
- `conversations/services.py` réserve aux administrateurs le nom, la photo, la permission d’envoi, le retrait et le changement de rôle. Le créateur ne peut pas être retiré et le dernier administrateur ne peut pas être rétrogradé.
- L’envoi est refusé aux membres lorsque le groupe est en mode administrateurs uniquement, y compris via WebSocket.
- La recherche conversations/contacts et les routes d’administration ont été ajoutées aux sélecteurs, sérialiseurs, vues et URLs de `conversations`.

### Temps réel et multi-appareils

- Le consumer de conversation contrôle toujours l’appartenance à chaque événement et accepte maintenant `message.edit`, `message.delete` et `reaction.set`.
- Le nouveau consumer `/ws/users/me/` ajoute chaque onglet/appareil au groupe `user.{id}`. Toutes les sessions reçoivent nouveaux messages, modifications, suppressions, réactions, lectures et changements de groupe.
- La présence et la saisie restent limitées à la conversation ouverte; les événements persistants sont publiés à la fois au groupe conversation et aux groupes utilisateurs.
- `frontend/lib/realtime/use-user-realtime.ts` maintient ce flux pendant la session et synchronise Zustand. `upsertMessage` et `updateReceipt` rendent sans effet les doublons reçus par deux flux.

### Frontend

- `message-bubble.tsx` fournit réactions rapides, compteurs, clic droit desktop et appui long de 550 ms sur mobile. Modifier/supprimer ne sont visibles que pour l’auteur. Le menu est ancré sous la bulle pour ne pas dépasser à 375 px.
- `message-thread.tsx` branche les actions, le sélecteur multi-conversations et le défilement vers le résultat de recherche.
- `chat-header.tsx` ajoute recherche interne, surlignage, compteur et navigation entre occurrences.
- `conversation-list.tsx` recherche conversations et contacts via REST, avec filtrage local pour les requêtes courtes.
- `info-panel.tsx` montre les commandes sensibles uniquement aux administrateurs et confirme le retrait d’un membre; le backend reste l’autorité finale.
- `chat-shell.tsx` coordonne hooks React Query, état Zustand, erreurs, actions et désactivation du composeur selon le droit d’envoi.
- Types, hooks API et store ont été étendus sans appel réseau direct dans les composants visuels.
- `notification-prompt.tsx` détecte iOS/iPadOS et le mode standalone via `navigator.standalone` ou `display-mode: standalone`. Hors standalone sur iOS, seules les étapes « Partager → Ajouter à l’écran d’accueil » sont affichées et aucune permission n’est demandée. Ailleurs, la permission reste liée au bouton explicite « Activer les notifications ».
- `README.md` et `frontend/README.md` documentent routes, événements, recherche, interactions et notifications iOS.

### Difficultés et solutions

1. `pytest` n’était pas dans le `PATH` PowerShell : utilisation portable de `python -m pytest`.
2. Une commande de migration a d’abord été lancée depuis `frontend/`, où `manage.py` n’existe pas. Le smoke test groupé a réussi puis la migration a été relancée depuis la racine; aucune donnée n’a été modifiée par l’erreur.
3. Une recherche calculée sans index aurait mal évolué : ajout d’un index GIN fonctionnel, partiel et créé concurremment sur PostgreSQL.
4. Le seul socket de conversation ne synchronisait pas les appareils affichant une autre vue : ajout complémentaire du flux persistant par utilisateur.
5. La suppression physique aurait cassé audit et statuts : utilisation d’une suppression logique globale et d’un masquage personnel séparé.
6. Le premier build a dépassé la limite de 120 secondes pendant que le worker compilait encore. Il a été surveillé jusqu’à sa fin, puis relancé seul avec une limite adaptée et la télémétrie désactivée; les builds suivants ont réussi.
7. Le placement latéral initial du menu contextuel pouvait déborder sur téléphone : ancrage sous la bulle selon son alignement.

### Vérifications finales

- `python -m pytest` : 18 tests réussis, couvrant les actions, recherches, permissions et deux sessions WebSocket simultanées recevant le même message et la même lecture.
- `python manage.py check --settings=kozons.settings.local` : aucun problème.
- `python manage.py makemigrations --check --dry-run --settings=kozons.settings.test` : aucune migration manquante.
- `npm run typecheck` : TypeScript strict sans erreur.
- `npm run build` : compilation optimisée, validation des types, export de 11 pages et génération de `public/sw.js` avec repli `/offline.html` réussis après le dernier correctif.
- `npm run test:responsive` : réussi à 375×812, 768×1024 et 1440×900, sans erreur runtime ni débordement, avec connexion initiale, lien d’inscription et aucune donnée fictive.
- Migrations locales `conversations.0003`, `messaging.0003` et `messaging.0004` appliquées.
- Aucun seed ni compte fictif ajouté; les tests utilisent une base SQLite en mémoire isolée.
- Frontend, API et Daphne relancés avec le nouveau code sur `0.0.0.0:3000`, `0.0.0.0:8000` et `0.0.0.0:8001`. La page de connexion et `/api/health/` répondent HTTP 200.

### Résultat

Toutes les fonctionnalités demandées sont intégrées dans les couches modèle, service, API, WebSocket, hooks, état global et interface. En production, il faudra appliquer les migrations PostgreSQL avant déploiement et conserver Redis comme channel layer pour la diffusion multi-processus et multi-appareils.
