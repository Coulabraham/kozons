# Backend Kozons

Le frontend PWA Next.js se trouve dans `frontend/`. Son installation, ses variables d’environnement et ses commandes de validation sont documentées dans `frontend/README.md`.

Backend de chat temps réel construit avec Django, Django REST Framework, Channels, Redis, Celery, PostgreSQL et un stockage compatible S3.

## Architecture

Les responsabilités sont séparées en six applications :

- `users` : utilisateur personnalisé, inscription, OTP, connexion JWT et fournisseurs SMS ;
- `contacts` : normalisation et synchronisation unidirectionnelle du carnet d’adresses ;
- `conversations` : conversations individuelles ou de groupe et rôles des membres ;
- `messaging` : historique par curseur, messages, accusés et consumer WebSocket ;
- `media` : URL d’upload S3 présignée et traitement FFmpeg par Celery ;
- `notifications` : abonnements Web Push et notifications VAPID asynchrones.

La logique métier réside dans les fichiers `services.py`; les vues restent une couche HTTP mince. Les lectures complexes sont isolées dans `selectors.py`.

Deux entrées de déploiement sont fournies :

- `kozons.wsgi` pour le trafic HTTP REST via Gunicorn ;
- `kozons.asgi` pour `/ws/` via Daphne et Channels.

En production, le proxy inverse doit envoyer `/api/` vers le service HTTP et `/ws/` vers le service ASGI. L’entrée ASGI sait aussi traiter HTTP, ce qui permet un déploiement monoprocessus plus simple si cette séparation n’est pas nécessaire.

## Démarrage avec Docker

```bash
cp .env.example .env
docker compose up --build -d postgres redis minio minio-init
docker compose run --rm http python manage.py migrate
docker compose run --rm http python manage.py seed_kozons
docker compose up -d http realtime worker beat clamav
```

Services exposés : API REST sur `http://localhost:8000`, WebSocket sur `ws://localhost:8001`, S3 sur `http://localhost:9000` et console MinIO sur `http://localhost:9001`.

Le seed est idempotent et réservé au développement. Il crée quatre utilisateurs, des contacts, deux conversations individuelles, un groupe et plusieurs types de messages.

## Exécution locale sans Docker

Installer PostgreSQL, Redis et FFmpeg, puis :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Charger dans le shell les variables de .env.example après les avoir remplacées.
python manage.py migrate
python manage.py runserver
celery -A kozons worker -l INFO
daphne -p 8001 kozons.asgi:application
```

Sous Windows, l’activation est `.venv\\Scripts\\activate` et Celery peut nécessiter `--pool=solo` en développement.

### Profil local sans Docker

Lorsque PostgreSQL et Redis ne sont pas disponibles, `kozons.settings.local` utilise une base SQLite locale vide, le cache mémoire et Celery synchrone. Il ne crée aucun seed. Les secrets de repli et l’OTP `000000` de ce profil sont explicitement réservés au développement ; `prod.py` ne les utilise pas. Lancer :

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000 --noreload --settings=kozons.settings.local
python -m daphne -b 127.0.0.1 -p 8001 kozons.asgi_local:application
```

Pour un parcours OTP local sans fournisseur SMS, `OTP_FIXED_CODE=000000` peut être défini uniquement avec ce profil. `prod.py` refuse explicitement cette variable.

Pour tester depuis un autre appareil connecté au même Wi-Fi, relever l’adresse IPv4 du PC avec `ipconfig`, puis ajouter l’origine frontend dans le shell qui lance Django :

```powershell
$env:KOZONS_LOCAL_NETWORK_ORIGINS="http://192.168.1.3:3000" # facultatif : les interfaces privées sont aussi détectées
python manage.py runserver 0.0.0.0:8000 --noreload --settings=kozons.settings.local
python -m daphne -b 0.0.0.0 -p 8001 kozons.asgi_local:application
```

Ouvrir ensuite `http://192.168.1.3:3000` sur le téléphone. Remplacer l’adresse si `ipconfig` en indique une autre. Le téléphone et le PC doivent être sur le même réseau, et le pare-feu Windows doit autoriser Python et Node.js sur les réseaux privés.

## API REST

| Méthode | Route | Description |
|---|---|---|
| POST | `/api/auth/register/` | Crée un compte inactif et envoie un OTP |
| POST | `/api/auth/verify-otp/` | Active le compte avec un code à six chiffres |
| POST | `/api/auth/login/` | Retourne l’access JWT et pose le refresh en cookie HttpOnly |
| POST | `/api/auth/refresh/` | Renouvelle et fait tourner le refresh cookie |
| POST | `/api/auth/logout/` | Révoque le refresh courant |
| POST | `/api/auth/logout-all/` | Révoque immédiatement tous les tokens de l’utilisateur |
| POST | `/api/auth/change-password/` | Change le mot de passe et révoque toutes les sessions |
| POST | `/api/contacts/sync/` | Normalise jusqu’à 1 000 numéros et ajoute les inscrits trouvés |
| GET | `/api/conversations/` | Liste les conversations et leurs membres |
| POST | `/api/conversations/` | Crée ou retrouve une conversation individuelle, ou crée un groupe |
| GET | `/api/conversations/{id}/messages/` | Historique paginé par curseur |
| POST | `/api/conversations/{id}/messages/` | Solution REST de repli pour envoyer un message |
| POST | `/api/media/presign/` | Crée un média et une politique d’upload présignée |
| POST | `/api/media/{id}/complete/` | Vérifie l’objet et lance son traitement Celery |
| POST | `/api/notifications/subscriptions/` | Enregistre un abonnement Web Push |

Toutes les routes sauf l’inscription, la vérification OTP, la connexion et le refresh exigent `Authorization: Bearer <access>`.

## WebSocket

Connexion navigateur (le token voyage en sous-protocole, pas dans l’URL) :

```text
new WebSocket("ws://localhost:8001/ws/conversations/{conversation_id}/", ["kozons", "kozons.jwt.{access_token}"])
```

Un en-tête `Authorization: Bearer <access_token>` est aussi accepté pour les clients natifs. La query string est limitée au développement/tests. Le middleware valide le JWT et le consumer revalide l’appartenance avant chaque événement entrant et sortant.

Un consumer par conversation a été retenu : l’autorisation est directe, les groupes Redis correspondent exactement aux domaines de diffusion, et un événement n’est jamais envoyé à une conversation non ouverte par le client. Une connexion par utilisateur aurait réduit le nombre de sockets pour un écran global, mais aurait imposé un routage applicatif supplémentaire pour chaque événement.

Événements client :

```json
{"event":"message.send","client_id":"UUID","message_type":"texte","contenu":"Bonjour"}
{"event":"message.send","client_id":"UUID","message_type":"video","media_asset_id":123}
{"event":"receipt.update","message_id":42,"status":"recu"}
{"event":"receipt.update","message_id":42,"status":"lu"}
{"event":"typing","is_typing":true}
{"event":"presence.heartbeat"}
```

Événements serveur : `message.new`, `receipt.updated`, `typing.changed`, `presence.changed`, `presence.heartbeat.ack` et `error`.

`client_id` rend l’envoi idempotent lors d’une reconnexion. Les statuts ne peuvent avancer que de `envoye` vers `recu`, puis `lu`. La présence accepte plusieurs connexions par utilisateur grâce à un `ZSET` Redis et expire après 60 secondes sans heartbeat.

## Fonctions de messagerie avancées

Les opérations persistantes restent dans les services Django et sont exposées par des vues DRF minces :

- `PATCH /api/messages/{id}/` modifie un message texte de l’expéditeur et renseigne `modifie_le` ;
- `DELETE /api/messages/{id}/?mode=me|everyone` masque le message pour son auteur ou le supprime logiquement pour tous pendant la fenêtre configurée par `MESSAGE_DELETE_FOR_EVERYONE_HOURS` (48 h par défaut) ;
- `POST /api/messages/{id}/forward/` transfère le texte ou la référence média vers une à vingt conversations accessibles ;
- `POST` et `DELETE /api/messages/{id}/reaction/` posent, remplacent ou retirent l’unique réaction de l’utilisateur ;
- `GET /api/conversations/{id}/messages/search/?q=...` effectue une recherche plein texte ;
- `GET /api/conversations/search/?q=...` cherche les conversations et les contacts par nom ;
- `PATCH /api/conversations/{id}/`, `DELETE /api/conversations/{id}/members/{user_id}/` et `PATCH /api/conversations/{id}/members/{user_id}/role/` appliquent les permissions d’administration de groupe.

Le flux `/ws/users/me/` complète le flux de la conversation ouverte. Chaque onglet ou appareil rejoint le même groupe Channels `user.{id}` : nouveaux messages, modifications, suppressions, réactions, accusés de lecture et changements de groupe atteignent ainsi toutes les sessions actives. Les événements ajoutés sont `message.updated`, `message.deleted`, `message.hidden`, `reaction.updated` et `conversation.changed`.

PostgreSQL dispose de l’index GIN partiel `message_contenu_fts_idx` sur le vecteur français des messages texte non supprimés. Sa migration utilise `CREATE INDEX CONCURRENTLY` afin de limiter le verrouillage en production ; SQLite l’ignore volontairement et utilise `icontains` dans les tests et le profil local.

## Historique à grand volume

L’index `(id_conversation, date_envoi DESC, id DESC)` suit exactement l’ordre de lecture. Le curseur DRF encode le couple date/identifiant du dernier élément ; aucune page n’utilise `OFFSET`. `id` assure un ordre total lorsque plusieurs messages partagent la même date.

Pour plusieurs dizaines de millions de lignes, surveiller `EXPLAIN (ANALYZE, BUFFERS)`, autovacuum et la taille de l’index. Une évolution par partitions mensuelles exige une clé primaire incluant `date_envoi` dans PostgreSQL. Si `id` doit rester la clé globale unique, conserver la table chaude et déplacer les périodes anciennes vers une table d’archive est moins intrusif.

## Médias

Le client demande une URL présignée avec le type logique, le MIME, la taille et éventuellement la conversation. Le serveur impose une liste MIME et une taille maximale. Après l’upload direct vers S3, l’appel `complete` vérifie l’objet avec `HeadObject`; le worker valide ensuite sa signature binaire et l’analyse avec ClamAV avant publication et traitement FFmpeg.

- vidéo : H.264/AAC MP4, CRF 27, largeur maximale 1280 px et miniature JPEG ;
- note vocale : Opus mono à 48 kbit/s dans un conteneur OGG ;
- image : conservée telle quelle dans cette version.

Les commandes FFmpeg utilisent une liste d’arguments et jamais un shell. Les chemins contiennent des HMAC opaques et des UUID, sans téléphone, email ou nom original. La base conserve des références `s3://` ; les téléchargements publics doivent utiliser des URL signées courtes.

## OTP, SMS et notifications

Les OTP sont hachés, valables cinq minutes, limités à cinq essais et protégés par des compteurs de débit sans identifiant en clair dans la clé Redis. `SMS_PROVIDER` sélectionne `ConsoleSMSProvider`, `TwilioSMSProvider` ou `AfricasTalkingSMSProvider` sans modifier le service d’inscription.

En développement local, aucun message externe n’est envoyé par défaut. Avec `OTP_FIXED_CODE=000000` et `NEXT_PUBLIC_LOCAL_OTP_CODE=000000`, l’écran de vérification affiche un bouton permettant de remplir ce code. Ces deux variables sont strictement réservées au poste de développement et doivent être absentes en production.

Pour recevoir réellement un OTP par e-mail, copier la section SMTP de `.env.example` dans le fichier `.env`, renseigner le compte expéditeur et son mot de passe d’application, puis redémarrer les processus Django et Celery. Avec Gmail, la validation en deux étapes doit être activée sur le compte expéditeur afin de créer un mot de passe d’application ; le mot de passe Gmail principal ne doit jamais être utilisé ni communiqué. Supprimer `NEXT_PUBLIC_LOCAL_OTP_CODE` du frontend dès que l’envoi réel est activé.

Pour les inscriptions par téléphone, sélectionner `users.sms.TwilioSMSProvider` ou `users.sms.AfricasTalkingSMSProvider` dans `SMS_PROVIDER`, renseigner les variables correspondantes et redémarrer le worker Celery. Le fournisseur console ne livre aucun SMS.

### Activer les OTP e-mail avec Gmail

1. Activer la validation en deux étapes du compte Google expéditeur.
2. Créer un mot de passe d’application Google de 16 caractères. Cette option exige la validation en deux étapes et peut être indisponible pour certains comptes professionnels, comptes sous Protection Avancée ou configurations utilisant uniquement des clés de sécurité.
3. Définir les variables suivantes dans le shell du backend, sans les enregistrer dans Git :

```powershell
$env:EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST="smtp.gmail.com"
$env:EMAIL_PORT="587"
$env:EMAIL_USE_TLS="true"
$env:EMAIL_USE_SSL="false"
$env:EMAIL_HOST_USER="adresse-expediteur@gmail.com"
$env:EMAIL_HOST_PASSWORD="MOT_DE_PASSE_APPLICATION_SANS_ESPACES"
$env:DEFAULT_FROM_EMAIL=$env:EMAIL_HOST_USER
$env:KOZONS_USE_RANDOM_OTP="true"
```

Redémarrer ensuite Django et le worker Celery. En profil local, Celery est synchrone et le redémarrage de Django suffit. Supprimer également `NEXT_PUBLIC_LOCAL_OTP_CODE` de `frontend/.env.local`, puis redémarrer Next.js. La procédure officielle Google est disponible dans [l’aide sur les mots de passe d’application](https://support.google.com/accounts/answer/185833?hl=fr).

### Activer les OTP SMS avec Twilio

Créer un compte Twilio, obtenir un numéro autorisé à envoyer des SMS, puis récupérer le SID et le jeton depuis la console. Les numéros destinataires et expéditeurs doivent utiliser le format international E.164, par exemple `+221...`.

```powershell
$env:SMS_PROVIDER="users.sms.TwilioSMSProvider"
$env:TWILIO_ACCOUNT_SID="AC..."
$env:TWILIO_AUTH_TOKEN="SECRET_TWILIO"
$env:TWILIO_FROM_NUMBER="+1..."
$env:KOZONS_USE_RANDOM_OTP="true"
```

Redémarrer Django et Celery après modification. Un compte Twilio d’essai peut limiter l’envoi aux destinataires préalablement vérifiés et certains pays imposent l’enregistrement de l’expéditeur. Voir la [documentation officielle Twilio](https://www.twilio.com/docs/messaging/tutorials/how-to-send-sms-messages).

Africa’s Talking reste disponible en alternative avec `SMS_PROVIDER=users.sms.AfricasTalkingSMSProvider`, `AFRICASTALKING_USERNAME`, `AFRICASTALKING_API_KEY` et, facultativement, `AFRICASTALKING_SENDER_ID`.

Ne jamais utiliser le mot de passe principal Gmail, ni placer un mot de passe d’application, un jeton Twilio ou une clé Africa’s Talking dans `.env.example`, le dépôt Git, les journaux ou `rapport.md`.

La configuration complète, le modèle de confiance et la checklist de mise en production sont dans [`SECURITY.md`](SECURITY.md).

Les notifications Web Push utilisent VAPID. Les abonnements retournant HTTP 404 ou 410 sont désactivés. Aucun push n’est créé pour un destinataire actuellement présent dans Redis.

## Tests

```bash
pytest
```

Le réglage `kozons.settings.test` utilise SQLite en mémoire, un channel layer en mémoire, un cache local, Celery synchrone et l’OTP fixe `000000`. Il ne doit jamais être utilisé hors tests.
