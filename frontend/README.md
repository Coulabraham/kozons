# Frontend Kozons

PWA de messagerie construite avec Next.js 15, TypeScript strict, Tailwind CSS, Zustand, React Query, Socket.IO Client, `date-fns` et `next-pwa`.

## Démarrage

```powershell
Copy-Item .env.example .env.local
npm install
npm run dev
```

Le frontend ne contient plus de données de démonstration : il nécessite le backend Kozons pour créer un compte et charger les conversations. Pour utiliser Django Channels, conserver `NEXT_PUBLIC_REALTIME_TRANSPORT=channels`. La variante `socketio` active le transport Socket.IO lorsqu’une passerelle compatible est déployée.

## Variables publiques

- `NEXT_PUBLIC_API_URL` : origine de l’API REST ; vide, elle utilise l’hôte courant sur le port 8000 ;
- `NEXT_PUBLIC_SOCKET_URL` : origine de la couche temps réel ; vide, elle utilise l’hôte courant sur le port 8001 ;
- `NEXT_PUBLIC_REALTIME_TRANSPORT` : `channels` ou `socketio` ;
- `NEXT_PUBLIC_VAPID_PUBLIC_KEY` : clé publique nécessaire à l’abonnement Web Push.

Lorsque l’URL configurée utilise `localhost` ou `127.0.0.1`, le navigateur remplace automatiquement cet hôte par celui utilisé pour ouvrir Kozons. Un téléphone ouvrant `http://192.168.1.3:3000` contactera donc l’API sur `192.168.1.3:8000` et Channels sur `192.168.1.3:8001`. Le backend doit être lancé sur `0.0.0.0` et cette origine doit figurer dans `KOZONS_LOCAL_NETWORK_ORIGINS`.

## Validation

```powershell
npm run typecheck
npm run build
npm run test:responsive
```

Le test responsive utilise Microsoft Edge et son protocole DevTools, sans bibliothèque additionnelle. Il vérifie les vues 375×812, 768×1024 et 1440×900, l’absence de débordement horizontal, la pile de navigation mobile et le panneau d’informations desktop. `EDGE_PATH` et `KOZONS_PREVIEW_URL` permettent d’adapter le test à un autre poste.

Après `npm run build`, `npm start` sert l’export statique depuis `out/`. Le service worker ne met en cache que les assets publics : il ne partage jamais une réponse API authentifiée entre deux comptes. Zustand persiste les conversations déjà chargées pour le mode hors ligne minimal et ce cache privé est purgé à la déconnexion.

Le refresh JWT reste exclusivement dans un cookie `HttpOnly`; seul l’access court est conservé en mémoire. En production, utiliser uniquement des origines HTTPS/WSS et définir `KOZONS_CSP_CONNECT_SRC` sur le serveur statique si l’API n’est pas sur la même origine.

## Organisation

- `app/` : routes App Router et configuration globale ;
- `components/` : composants visuels découplés du réseau ;
- `lib/api/` : client REST et hooks React Query ;
- `lib/realtime/` : adaptateurs Channels et Socket.IO ;
- `lib/notifications/` : abonnement Web Push déclenché au moment opportun ;
- `store/` : état Zustand persistant ;
- `scripts/` : serveur statique et smoke test responsive.

Les médias sont envoyés directement vers S3 à l’aide d’un formulaire pré-signé, puis finalisés par l’API. Les avatars utilisent un `avatar_media_id` validé côté serveur : PostgreSQL conserve la référence S3 durable et l’API expose une URL de lecture courte.

## Messagerie avancée et notifications iOS

Les bulles proposent les réactions rapides au survol et un menu au clic droit sur ordinateur ou après un appui long sur mobile. Les actions modifier et supprimer sont réservées à l’auteur. Le transfert ouvre un sélecteur multi-conversations. La recherche générale interroge conversations et contacts ; la recherche de l’en-tête d’une discussion surligne les occurrences et permet de naviguer entre elles.

Le panneau d’un groupe n’affiche les commandes de nom, photo, permission d’envoi, promotion, rétrogradation et retrait qu’aux administrateurs. Le backend revalide toutefois toujours les droits : masquer un bouton ne constitue pas une mesure de sécurité.

Sur iOS/iPadOS hors mode standalone, Kozons affiche les étapes **Partager → Ajouter à l’écran d’accueil** et ne demande pas la permission de notification. Une fois la PWA lancée depuis son icône, ou sur Android/ordinateur, l’autorisation reste déclenchée uniquement par le bouton explicite **Activer les notifications**.
