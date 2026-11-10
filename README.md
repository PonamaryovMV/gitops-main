# Ветка ФП qa/bt

Сюда пишет только Jenkins (`qa-bt/BuildRelease`). Каждый коммит = релиз = Freight в Kargo-проекте `qa-bt`.

- `qa/bt/<сервис>/release.yaml` — версия сервиса в релизе;
- `qa/bt/release-plan.yaml` — порядок выкатки по волнам, посчитан из `deploy.dependsOn` в values окружений (ветка `main`).
