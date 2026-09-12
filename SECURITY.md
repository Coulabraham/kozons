# Sécurité de Kozons

## Modèle de confiance

L’API REST et le serveur Channels sont deux processus distincts derrière un proxy TLS. PostgreSQL, Redis, Celery, ClamAV et le stockage S3 restent sur un réseau privé. Le bucket est privé : seules des politiques d’upload et des URL de lecture valables 300 secondes sont remises aux clients.

## Configuration Django ajoutée

| Élément | Configuration | Raison |
|---|---|---|
| Mots de passe | `Argon2PasswordHasher` en premier, PBKDF2 conservé pour migration progressive ; longueur minimale 10, contrôles courant/similaire/numérique | Hash mémoire-dur et politique raisonnable |
| JWT | access 10 min, refresh 30 jours, rotation + blacklist, claim `ver`, cookie refresh `HttpOnly`, `Secure`, `SameSite=Strict` | Réduit le vol par XSS et permet logout, révocation globale et changement de mot de passe |
| Middleware | `SecurityMiddleware`, `CorsMiddleware` placé haut, `SecurityHeadersMiddleware`, `XFrameOptionsMiddleware` | HTTPS/HSTS en production, CORS explicite, CSP API, anti-sniffing et anti-framing |
| Cookies | `Secure`, `HttpOnly`, `SameSite=Strict` ; contrôle `Origin`/`Sec-Fetch-Site` sur refresh/logout | Réduction des risques XSS/CSRF |
| CORS | `CORS_ALLOWED_ORIGINS` explicite, credentials limités, uniquement `/api/` | Aucun joker en production |
| WebSocket | `OriginValidator` avec `WEBSOCKET_ALLOWED_ORIGINS` | Bloque les origines navigateur non autorisées |
| Secrets | variables d’environnement obligatoires en production, longueur minimale de 32 caractères pour les secrets applicatifs | Aucun secret opérationnel dans le dépôt |

En production, `prod.py` refuse de démarrer sans secrets distincts, hôtes explicites, origines HTTPS, fournisseur SMS réel, ou si un OTP fixe est configuré. Le proxy doit transmettre `X-Forwarded-Proto` après avoir supprimé toute valeur fournie par le client.

## Throttling DRF et compteurs Redis

Trois classes s’appliquent : `BurstRateThrottle` (`60/min`), `SustainedRateThrottle` (`1000/day`) et `ScopedRateThrottle`. Les scopes sont : inscription `20/hour`, login `100/hour`, OTP `60/hour`, renvoi OTP `20/hour`, contacts `10/hour`, messages `120/min`, uploads `30/hour`, opérations de session `30/hour`.

Ces limites DRF sont une défense générale. Les limites critiques sont également imposées dans les services via des clés HMAC Redis, ce qui couvre REST et WebSocket :

- inscription : 5/15 min par identifiant et 20/h par IP ;
- connexion : 10/15 min par identifiant et 60/15 min par IP ;
- validation OTP : 5/15 min par identifiant et 30/15 min par IP ;
- renvoi OTP : 3/15 min par identifiant et 20/h par IP ;
- message : 120/min par utilisateur ; upload : 30/h par utilisateur.

`DRF_NUM_PROXIES` doit correspondre exactement au nombre de proxies maîtrisés. Les limites applicatives ne remplacent pas une protection DDoS/WAF à l’entrée réseau.

## Authentification Channels

Le navigateur transmet l’access JWT dans le sous-protocole `kozons.jwt.<token>` ; il n’apparaît donc pas dans l’URL. L’en-tête `Authorization` reste accepté pour les clients natifs. La query string n’est autorisée qu’en dev/test et est interdite par `prod.py`.

À la connexion, `RevocableJWTAuthentication` valide signature, expiration, utilisateur actif et version de révocation. Le consumer vérifie l’appartenance à la conversation avant de rejoindre le groupe, avant chaque événement entrant (`message.send`, accusé, saisie, heartbeat) et avant chaque événement sortant. Une révocation d’appartenance ferme la connexion avec le code 4403.

## Contacts et vie privée

Les sérialiseurs de tiers ne retournent jamais `telephone` ni `email`. Les réponses de synchronisation et les membres d’une conversation exposent seulement l’identifiant interne, le nom, l’avatar et le statut public. Les identifiants présents dans Redis et dans le journal d’audit sont pseudonymisés par HMAC.

Le simple SHA-256 côté client n’est **pas** retenu : l’espace des numéros est assez petit pour une attaque par dictionnaire et le hash deviendrait un identifiant stable corrélable. L’étape avancée à étudier avant un déploiement à grande échelle est un protocole PSI/OPRF audité, ou une recherche par préfixe k-anonyme avec protection anti-énumération. En attendant, la liste brute transite uniquement sous TLS, est limitée à 1 000 entrées, n’est pas journalisée et la réponse est expurgée.

## Médias

La demande de presign impose type logique, liste MIME et taille maximale (20 Mio image, 250 Mio vidéo, 30 Mio audio). La politique S3 répète le type et la borne de taille. Après upload, `HeadObject` vérifie taille et MIME ; le worker télécharge dans un dossier temporaire, vérifie la signature binaire, puis transmet le flux à ClamAV avant toute publication ou conversion FFmpeg. Un fichier invalide/infecté est marqué en échec et supprimé du bucket source.

Les noms utilisent UUID + HMAC de la portée utilisateur/conversation, sans nom original, téléphone ou email. La base garde des références `s3://` internes ; les API n’exposent que des URL GET présignées courtes. Le bucket doit bloquer tout accès public et appliquer chiffrement, politique de cycle de vie et CORS S3 restrictif.

## Texte et XSS

Le serveur valide tous les types et longueurs, normalise les messages en Unicode NFC et refuse NUL/caractères de contrôle. Le HTML n’est jamais rendu comme HTML : React effectue l’échappement contextuel via les nœuds texte et aucune utilisation de `dangerouslySetInnerHTML` n’existe. Conserver le texte original, puis encoder à la sortie, évite les transformations destructrices tout en bloquant l’exécution XSS. Toute future fonction Markdown/HTML devra utiliser un sanitiseur à liste blanche maintenu.

## Journal d’audit

`SecurityAuditEvent` enregistre inscription, validation OTP, connexion, logout, logout global, changement de mot de passe et modification de profil. IP et identifiant ciblé sont HMACés ; mots de passe, OTP et JWT ne sont jamais consignés. Une rétention courte, un accès restreint et un export vers un SIEM immuable doivent être définis en production. Le futur workflow de suppression de compte devra émettre `account_deletion_requested/completed`.

## Checklist finale

| Contrôle | Statut | Justification / reste à faire |
|---|---|---|
| Argon2 et politique de mot de passe | **Fait** | Argon2 premier hasher, minimum 10, validateurs Django et test dédié |
| Access JWT court, rotation, blacklist, révocation | **Fait** | 10 min, rotation/blacklist, cookie HttpOnly, claim de version, purge quotidienne Celery Beat |
| OTP unique, 5 min, 5 essais | **Fait** | Hash en base, verrou SQL, consommation unique ; les essais échoués sont persistés hors rollback |
| Anti-spam OTP par IP et identité | **Fait** | Compteurs HMAC Redis dans les services + scopes DRF |
| Auth WebSocket et autorisation par événement | **Fait** | JWT révocable, origine validée, contrôle d’appartenance entrant et sortant |
| Masquage téléphone/email des tiers | **Fait** | `PublicUserSerializer`, régression testée |
| Synchronisation privée PSI/OPRF | **À faire** | Conception recommandée ; ne pas déployer un hash SHA-256 naïf |
| Validation médias taille/MIME/signature | **Fait** | Contrôle avant publication et listes fermées |
| Antivirus | **Fait dans le code / à valider en infrastructure** | ClamAV fail-closed activé par défaut en prod et service Compose ajouté ; tester signatures EICAR, disponibilité et charge |
| URL S3 courtes et noms opaques | **Fait** | 300 s, UUID/HMAC, aucune référence interne dans les réponses de suivi |
| HTTPS/WSS, HSTS | **Fait dans Django / à valider au proxy** | Redirection SSL et HSTS 1 an ; certificats, preload et headers proxy relèvent du déploiement |
| CORS/CSP/en-têtes | **Fait** | Origines explicites, CSP API et serveur statique, nosniff, DENY, referrer/permissions policy |
| Rate limiting sensible | **Fait** | Défense DRF + compteurs Redis partagés REST/WS ; ajouter WAF/DDoS en production |
| Audit des actions sensibles existantes | **Fait** | Événements pseudonymisés en base et logs |
| Audit de suppression de compte | **À faire** | Aucun workflow de suppression n’existe encore ; ajouter événements demandé/terminé lors de son implémentation |
| Validation entrées et XSS | **Fait** | Validation serveur, normalisation/rejet contrôles, échappement React à la sortie |
| Secrets hors code | **Fait** | `.env.example` sans valeur réelle, contrôles fail-fast prod, Compose alimenté par variables |
| Tests de pénétration et observabilité | **À faire** | Exécuter DAST, test de charge des limites, alertes SIEM et revue d’infrastructure avant ouverture publique |

## Exploitation avant production

1. Générer quatre secrets distincts avec un CSPRNG ; ne jamais réutiliser les exemples.
2. Terminer TLS au proxy, n’accepter que HTTPS/WSS, isoler PostgreSQL/Redis/S3/ClamAV et utiliser TLS aussi entre zones réseau non fiables.
3. Rendre le bucket privé, configurer chiffrement et CORS, puis tester l’expiration des signatures.
4. Lancer migrations, Celery worker **et Celery Beat**, et superviser `flushexpiredtokens`.
5. Tester ClamAV avec EICAR en environnement isolé, les limites Redis en concurrence et le retrait d’un membre pendant une session WebSocket.
6. Définir rétention/accès du journal d’audit et des messages conformément aux obligations locales de protection des données.
