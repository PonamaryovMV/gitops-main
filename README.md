# gitops-main — ФП qa/at (dev, test, uat)

Конфигурация сервисов ФП `qa/at` в формате `<АС>/<ФП>/<сервис>/<окружение>/` и Kargo-проект, который её продвигает.
PROD живёт в отдельном репозитории [gitops-prod](https://github.com/PonamaryovMV/gitops-prod).

```
qa/at/<сервис>/<окружение>/          сервисы: mgmt, core, api   окружения: dev, test, uat
├── Chart.yaml                       umbrella-чарт: зависимость main 0.0.2 (oci://ghcr.io/ponamaryovmv/charts)
├── qa-at-<сервис>-<окружение>.yaml  values окружения (global.*, реплики, компоненты) — правят люди
└── release.yaml                     версия: main.container.version + list_image_build — пишет Kargo
kargo/qa-at/                         Kargo: Project, Warehouse, PromotionTask'и, Stages, DAST
                                     freight-alias.yaml — имена Freight = номер релиза (release-2-102)
demo-app/                            код демо-образов (собираются один раз workflow seed-images)
```

Ветка **`qa-at`** — ветка ФП. В ней только `qa/at/<сервис>/release.yaml`, пишет туда только Jenkins
(BuildRelease, ExcludeService). Kargo Warehouse смотрит на неё: каждый коммит Jenkins = Freight = снимок всех сервисов ФП.

## Флоу

```
Jenkins BuildRelease ──коммит release.yaml──▶ ветка qa-at ──▶ Kargo Warehouse → Freight
                                                                  │ Promote (вручную)
              dev ──▶ test ──▶ uat ──auto──▶ dast [Kargo → Jenkins qa-at/DAST] ──▶ prod (gitops-prod)
```

- Промоушен копирует `qa/at/<сервис>/release.yaml` из Freight в `qa/at/<сервис>/<окружение>/release.yaml` ветки `main`
  (для prod — в gitops-prod) и синкает Application'ы Argo CD. Values окружений не трогаются.
- `dast` — отдельная стадия без деплоя. Freight, развёрнутый на `uat`, попадает в неё автоматически (ProjectConfig),
  Kargo запускает Jenkins-джобу `qa-at/DAST` (параметр — список репозиториев) и ждёт её статус.
  Повтор DAST — Reverify на стадии `dast`. В prod можно продвинуть только Freight, прошедший `dast`.
- Исключение сервиса — Jenkins `qa-at/ExcludeService` (см. [jenkins](https://github.com/PonamaryovMV/jenkins)).

## release.yaml

```yaml
main:
  container:
    registry: ghcr.io/ponamaryovmv
    version: release-2-102            # тег всех образов сервиса
list_image_build:                     # вход SCA
  - ghcr.io/ponamaryovmv/qa-at-mgmt-api:release-2-102
  - ghcr.io/ponamaryovmv/qa-at-mgmt-worker:release-2-102
release:                              # служебное: откуда релиз и чем проверен
  task: TASK-2
  build: 12
  source: { repo: https://github.com/PonamaryovMV/qa-at-mgmt, commit: ... }   # вход SAST
  digests: { qa-at-mgmt-api: "sha256:...", qa-at-mgmt-worker: "sha256:..." }
  checks: { sca: PASSED, sast: PASSED }
```

## Образы

`ghcr.io/ponamaryovmv/qa-at-<сервис>-<компонент>:release-<N>-<сборка>` — сервисы `mgmt`, `core`, `api`,
компоненты `api`, `worker`, теги `release-1-101`, `release-2-102`, `release-3-103`.
Собраны один раз workflow **seed-images**; цвет страницы сервиса зависит от номера релиза.

## Проверка

Workflow **validate** рендерит каждую папку окружения через Helm так же, как Argo CD.
