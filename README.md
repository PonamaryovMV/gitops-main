# gitops-main — приложения стенда

Два тестовых приложения на Python (только stdlib, без зависимостей) с canary через Argo Rollouts
и промоушеном dev → stage → prod через Kargo.

```
apps/<app>/
├── src/              # app.py + Dockerfile (собирает scripts/build-app.sh)
├── base/             # Rollout (canary + анализ /health), Service stable/canary, AnalysisTemplate
├── envs/
│   ├── dev/          # ← сюда коммитит Kargo (newTag в kustomization.yaml)
│   ├── stage/
│   └── prod/
└── kargo/            # Project, ProjectConfig, Warehouse, PromotionTask, Stages, smoke-проверка
```

Argo CD подхватывает всё автоматически (ApplicationSet'ы в [infra](https://github.com/PonamaryovMV/infra)):

- `apps/<app>/envs/<env>` → Application `<app>-<env>` в неймспейсе `<env>`;
- `apps/<app>/kargo` → Application `kargo-<app>` (Kargo-проект `<app>`).

Новое приложение = скопировать папку, переименовать, поменять NodePort'ы в `envs/*` и порты в `scripts/config/kind-config.yaml`.

## Приложения

| | hello-api | color-web |
|---|---|---|
| Что | JSON API | страница с сеткой цветных квадратов: видно, какой под ответил |
| dev / stage / prod | localhost:8101 / 8102 / 8103 | localhost:8111 / 8112 / 8113 |
| Реплики dev / stage / prod | 1 / 2 / 3 | 1 / 2 / 3 |

Общие эндпоинты: `/version` (проверяет Kargo), `/health` (проверяет canary-анализ, `500` у сборки `--broken`), `/ready` (пробы).
color-web дополнительно ходит в `hello-api` своего неймспейса и показывает его версию.

## Пайплайн

1. `scripts/build-app.sh <app> X.Y.Z` пушит образ в локальный registry.
2. Warehouse (`kind-registry:5000/<app>`, SemVer) создаёт Freight.
3. Стейдж выполняет `PromotionTask/promote`: `git-clone` → `kustomize-set-image` в `envs/<stage>` → `git-commit` → `git-push` в `main` → `argocd-update`.
4. Argo Rollouts катит canary: 50% → 15с → анализ `/health` canary-подов (6 проверок) → 100%. Провал — откат на stable.
5. Kargo-верификация (`AnalysisTemplate/smoke`): стейдж отдаёт на `/version` ровно версию из Freight.
6. dev и stage продвигаются автоматически (`ProjectConfig`), prod — вручную.

Коммиты Kargo приходят в `main` от имени `Kargo <no-reply@kargo.io>` — перед своими правками делайте `git pull`.
