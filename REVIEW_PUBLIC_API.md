# Review complete de `public_api/`

Date de revue : 2026-04-29  
Etat revu : implementation courante de `public_api/`, contrat de gateway vers `auth_service`, `user_service`, `admin_service`, `content_service` et `worker_service`.

## Synthese executive

`public_api` remplit bien son role de facade FastAPI legere devant les microservices internes. Le decoupage est simple, les routers restent fins, la logique metier est majoritairement delegatee aux services amont, et les preoccupations publiques importantes sont deja centralisees ici : cookies de session, CORS, CSRF, rate limiting, mapping d'erreurs, auth admin/utilisateur.

Le service a donc une bonne base de gateway :

- surface applicative compacte et lisible ;
- dependances FastAPI/Pydantic/HTTP claires ;
- verification de session centralisee via `auth_service` ;
- garde-fous CSRF et cookies `HttpOnly` deja en place ;
- auth inter-service prevue via header dedie ;
- routes publiques et routes admin bien separees.

Verdict : bon socle pour dev et integration interne, mais pas encore au niveau d'une gateway publique vraiment robuste. Les principaux manques sont la disponibilite operationnelle (pas de readiness), un bug probable sur les releases workers exposees, une couverture de tests tres insuffisante, et quelques fragilites de securite/performance autour du rate limiting et des clients HTTP.

## Ce qui est bien

- Les routers deleguent proprement vers des services ou clients reseau.
- Les schemas de lecture/ecriture restent explicites et typés.
- La resolution de session passe par `auth_service` au lieu de dupliquer la logique de session.
- Le cookie de session est `HttpOnly`, `Secure` par defaut et borne au path `/`.
- La protection CSRF est appliquee a toutes les methodes dangereuses sous `/api/`.
- Les routes admin sont masquees derriere `NotFound` pour les non-admins sur plusieurs endpoints.
- Le client HTTP commun factorise correctement timeout, headers internes et mapping d'erreurs upstream.
- Le service reste stateless cote process, hors fallback memoire de rate limiting.

## Findings prioritaires

### Eleve - Les URLs de telechargement workers pointees par `public_api` ne sont pas servies par `public_api`

`public_api/app/routers/worker_release_router.py:12-38` recompose les `download_url` en `"{base_url}/workers/api/releases/download/{artifact_name}"`. En revanche, `public_api` n'expose aucune route `GET /workers/api/releases/download/{artifact_name}` dans `app/main.py:47-57`, alors que cette route existe bien dans `worker_service/app/routers/worker_release_router.py`.

Impact : la route publique des releases desktop peut renvoyer des URLs de telechargement cassées ou 404 cote gateway publique. Pour un client web ou desktop qui consomme `GET /workers/api/releases/desktop`, cela casse directement le workflow de telechargement.

Recommandation :

- Ajouter dans `public_api` une vraie route proxy/download vers `worker_service`, ou ne pas rewriter l'URL si la gateway ne sert pas effectivement le binaire.
- Ajouter un test d'integration qui verifie `list releases -> follow download_url -> 200`.
- Verifier aussi la coherence de `release_notes_url`, qui est force a `"{base_url}/workers"` sans route correspondante dans ce service.

### Eleve - Pas de readiness endpoint pour une gateway qui depend de plusieurs services critiques

`public_api/app/main.py:59-61` expose seulement `/internal/health`, une liveness statique. Il n'y a pas de `/internal/ready` qui verifie la presence des URLs upstream, la validite de la configuration CORS/CSRF/cookie, ni un ping minimal vers les services critiques.

Impact : une instance peut etre declaree "healthy" alors qu'elle ne peut pas authentifier un user, lire un compte, joindre Redis, ou atteindre les services amont. En Kubernetes/Compose/proxy, cela peut envoyer du trafic vers une gateway cassée mais vivante.

Recommandation :

- Ajouter `/internal/ready` avec verification minimale de config critique :
  `AUTH_SERVICE_URL`, `USER_SERVICE_URL`, `ADMIN_SERVICE_URL`, `CONTENT_SERVICE_URL`, `WORKER_SERVICE_URL` selon les routes exposees.
- Eventuellement faire un check reseau leger sur les upstreams essentiels.
- Echouer explicitement si `INTERNAL_SERVICE_TOKEN` manque en mode strict.

### Eleve - La couverture de tests est quasi nulle

Le seul test present est `public_api/tests/test_source_syntax.py:1-9`, qui verifie uniquement que les fichiers Python compilent. Aucun test ne couvre :

- login/logout/session cookie ;
- CSRF ;
- mapping d'erreurs upstream ;
- auth admin et masquage `404` ;
- rate limiting ;
- rewrite des URLs worker ;
- degradation quand un service amont est indisponible.

Impact : des regressions importantes dans la facade publique peuvent passer jusqu'en staging ou prod sans signal. Pour une gateway publique, c'est trop fragile.

Recommandation :

- Ajouter des tests unitaires et d'API FastAPI avec `TestClient`.
- Prioriser :
  `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/session`,
  les dependances auth, le middleware CSRF, et `worker_release_router`.
- Ajouter des tests de clients HTTP avec `httpx.MockTransport` ou client injecte.

### Moyen/Eleve - `register` est limite par IP seulement, pas par email/identifiant

`public_api/app/routers/auth_router.py:24-35` applique une limite `auth-register-ip`, alors que `login` cumule bien IP + email (`auth_router.py:38-56`).

Impact : avec des IP distribuees, un acteur peut bombarder le meme email ou pseudo avec des tentatives de creation de compte sans etre freine par identifiant cible. Cela augmente le bruit, l'enumeration indirecte et la pression sur `auth_service`.

Recommandation :

- Ajouter une limite complementaire par email normalise, et idealement par pseudo si pertinent.
- Aligner la politique avec celle deja appliquee a `login`.

### Moyen/Eleve - Changement de mot de passe : le cookie local est efface, mais la session serveur n'est pas explicitement revoquee

`public_api/app/routers/account_router.py:44-55` appelle `account_service.update_account_password(...)` puis `clear_session_cookie(response)`, sans appel a `auth_service.logout(...)` ni mecanisme visible de revocation de session.

Impact : la session courante semble seulement retiree du navigateur appelant. Si un token de session a fuite, rien dans cette gateway ne montre qu'il est invalide cote serveur apres changement de mot de passe. C'est un point de securite important.

Recommandation :

- Soit revoquer explicitement la session courante via `auth_service`,
- soit declencher une invalidation globale des sessions pour l'utilisateur,
- soit documenter clairement que `user_service` fait deja cette revocation en aval si c'est bien le cas.

Note : ce finding est une inference a partir du code de `public_api`; il faut confirmer le comportement effectif de `user_service`.

### Moyen - Clients HTTP sans pool de connexions

`public_api/app/clients/networking/service_http_client.py:55-72` instancie un nouveau `httpx.Client` dans un context manager a chaque requete quand aucun client n'est injecte.

Impact : perte de keep-alive, surcout TCP/TLS, latence evitable et pression supplementaire sur les upstreams. Pour une gateway, c'est un cout recurrent sur tous les flux.

Recommandation :

- Introduire des clients HTTP reutilisables par service au niveau process.
- Definir aussi des limites de pool et, si besoin, des timeouts plus fins par phase.

### Moyen - Rate limiting Redis non atomique et client Redis tres artisanal

Comme dans `auth_service`, `public_api/app/clients/networking/redis_networking_client.py:34-40` fait `INCR` puis `EXPIRE` seulement si le compteur vaut `1`. Le middleware `public_api/app/middleware/rate_limit.py:41-47` bascule ensuite sur erreur soit en echec ferme, soit en memoire.

Impact :

- si `EXPIRE` echoue apres `INCR`, une cle peut rester sans TTL ;
- le fallback memoire n'est pas partage entre replicas ;
- le client Redis ouvre une connexion socket par commande, ce qui reste simple mais peu performant.

Recommandation :

- Rendre `INCR + TTL` atomique via Lua ou une librairie Redis standard.
- Ajouter des tests autour du comportement de fallback et de l'indisponibilite Redis.
- Evaluer `redis-py` avec pool de connexions si le trafic public augmente.

### Moyen - Configuration de l'auth inter-service encore fragile si `APP_ENV` est mal regle

`public_api/app/security.py:28-35` fait primer `APP_ENV` sur `REQUIRE_INTERNAL_SERVICE_TOKEN`, comme dans `auth_service`.

Impact : un deploiement avec `APP_ENV=dev` peut desactiver en pratique l'exigence du token interne, meme si l'intention operationnelle etait de l'imposer. Comme `public_api` appelle plusieurs services internes, cette hygiene de config compte vraiment.

Recommandation :

- Faire primer explicitement `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.
- Ajouter des tests pour `APP_ENV=dev` combine a `REQUIRE_INTERNAL_SERVICE_TOKEN=true`.

### Moyen - Dependance Git non pinnee

`public_api/requirements.txt:7` depend de `manifeed-shared-backend` via `git+https://github.com/Manifeed/shared_backend.git@main`.

Impact : builds non reproductibles, changements de contrats ou d'exceptions sans modification locale, et debuggage plus difficile entre environnements.

Recommandation :

- Pinner sur tag ou commit SHA.
- Versionner les bumps de `shared_backend` comme une vraie mise a jour applicative.

### Moyen - Image Docker encore tres basique pour la prod

`public_api/Dockerfile:1-22` utilise `python:3.11-slim`, installe `git`, et lance l'application en root.

Impact : runtime plus large que necessaire, build dependant du reseau Git, et hardening container incomplet.

Recommandation :

- Introduire un utilisateur non-root.
- Retirer `git` de l'image runtime si la dependance Git disparait.
- Envisager un build multi-stage.

## Securite detaillee

### Session et cookies

Bon :

- cookie `HttpOnly` ;
- `Secure` par defaut ;
- `SameSite=Lax` ;
- lecture du token uniquement depuis le cookie de session.

Reste a faire :

- clarifier la politique de revocation apres changement de mot de passe ;
- ajouter des tests sur `Set-Cookie` et `Delete-Cookie` ;
- documenter les hypotheses proxy/TLS pour que `Secure` reste toujours coherent.

### CSRF

Bon :

- verification pour `POST`, `PUT`, `PATCH`, `DELETE` sous `/api/` ;
- normalisation propre des origins ;
- distinction dev/prod dans la resolution des origins de confiance.

Reste a faire :

- tests de non-regression pour les cas `Origin`, `Referer`, `x-forwarded-host`, `x-forwarded-proto` ;
- documentation claire des variables `CSRF_TRUSTED_ORIGINS`, `CORS_ORIGINS` et `CSRF_TRUST_SELF_ORIGIN`.

### Inter-service

Bon :

- header dedie `x-manifeed-internal-token` ;
- comparaison constant-time ;
- centralisation des headers internes dans le client commun.

Reste a faire :

- rendre la politique de strict mode moins fragile ;
- ajouter une readiness qui detecte un token absent en environnement strict.

### Rate limiting

Bon :

- middleware simple et reutilisable ;
- fallback memoire pratique en local ;
- echec ferme possible quand Redis est requis.

Reste a faire :

- atomicite Redis ;
- meilleure granularite des buckets ;
- observabilite minimale : compteur blocked/allowed/fallback.

## Architecture

Le decoupage reste coherent pour une gateway :

- `app/routers` : surface HTTP publique ;
- `app/dependencies` : auth et garde-fous d'acces ;
- `app/services` : facades applicatives minces ;
- `app/clients/networking` : appels inter-services ;
- `app/middleware` : CSRF et rate limiting ;
- `app/utils` : environnement et cookies ;
- `shared_backend` : contrats et erreurs partages.

Le service n'est pas sur-architecturé. En revanche, il reste encore tres peu "operationalisé" : peu de tests, peu de checks de readiness, pas de logs/metriques visibles, et peu de verification des contrats transverses.

## Scalabilite horizontale

Ce qui scale correctement :

- process stateless ;
- session resolue via `auth_service` ;
- logique metier delegatee aux services specialises ;
- fallback local limite au rate limiting en mode non strict.

Points a surveiller :

- un client HTTP neuf par requete ;
- un client Redis neuf par commande ;
- pas de cache local prudent pour certains reads frequents ;
- pas de garanties de readiness avant prise de trafic.

## Contrats API actuels

Routes publiques principales :

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/session`
- `GET /api/account/me`
- `PATCH /api/account/me`
- `PATCH /api/account/password`
- `GET /api/account/api-keys`
- `POST /api/account/api-keys`
- `DELETE /api/account/api-keys/{api_key_id}`
- `GET /api/sources`
- `GET /api/sources/{source_id}`
- `GET /api/sources/{source_id}/similar`
- `GET /api/rss/img/{icon_url}`
- `GET /workers/api/releases/desktop`

Routes admin principales :

- `GET /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `GET /api/admin/stats`
- `GET /api/admin/health/`
- `GET /api/admin/analysis/overview`
- `GET /api/admin/analysis/similar-sources`
- `GET /api/admin/jobs`
- `POST /api/admin/jobs/rss-scrape`
- `POST /api/admin/jobs/source-embedding`
- `GET /api/admin/jobs/automation`
- `PATCH /api/admin/jobs/automation`
- `GET /api/admin/jobs/{job_id}`
- `GET /api/admin/jobs/{job_id}/tasks`
- `GET /api/admin/rss/companies`
- `GET /api/admin/rss/`
- `POST /api/admin/rss/sync`
- `PATCH /api/admin/rss/feeds/{feed_id}/enabled`
- `PATCH /api/admin/rss/companies/{company_id}/enabled`
- `GET /api/admin/sources/`
- `GET /api/admin/sources/feeds/{feed_id}`
- `GET /api/admin/sources/companies/{company_id}`
- `GET /api/admin/sources/{source_id}`

Comportements a documenter explicitement :

- la gateway depend fortement de la disponibilite des services amont ;
- certaines routes admin masquent l'absence de privilege par `404` ;
- `logout` passe par une session cookie, pas par bearer public ;
- `GET /workers/api/releases/desktop` rewrite aujourd'hui les URLs de telechargement.

## Tests et verification

Tests presents :

- compilation syntaxique de tous les fichiers Python du service.

Verifications executees pendant cette revue :

- `python3 -m compileall -q public_api` : OK.

Limites de verification :

- `python3 -m pytest -q public_api/tests` n'a pas pu etre execute ici car `pytest` n'est pas installe dans l'environnement courant.
- Aucun test d'integration inter-services n'est present dans `public_api/tests/`.
- Pas de validation bout en bout des flows navigateur : login, cookie, CSRF, admin, worker releases.

## Plan d'action recommande

### P0 - Avant exposition plus large

- Corriger ou supprimer le rewrite des `download_url` workers tant que la route de download n'est pas servie par `public_api`.
- Ajouter un vrai endpoint `/internal/ready`.
- Ecrire des tests API FastAPI sur auth, CSRF, admin access et worker releases.
- Clarifier puis corriger la revocation de session apres changement de mot de passe.

### P1 - Stabilisation

- Ajouter un rate limit `register` par email/pseudo.
- Mutualiser des `httpx.Client` persistants.
- Rendre le rate limiting Redis atomique.
- Pinner `shared_backend`.
- Ajouter logs structures et quelques metriques gateway/upstream.

### P2 - Long terme

- Durcir l'image Docker.
- Formaliser des tests de contrat entre `public_api` et les services internes.
- Ajouter de l'observabilite orientee produit : taux de login, echec upstream, latence par service, hit rate limit, erreurs CSRF.
