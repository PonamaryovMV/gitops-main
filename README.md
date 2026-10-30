# Ветка ФП qa-at

Сюда пишет только Jenkins (BuildRelease, ExcludeService): `qa/at/<сервис>/release.yaml` — версия сервиса в релизе.
Kargo Warehouse `qa-at` смотрит на эту ветку: каждый коммит Jenkins = Freight = снимок всех сервисов ФП.
