# Makefile для управления systemd-сервисами PD Tradebot на VPS.
# Запускать из директории deploy/ под root: `make install`, `make start` и т. д.

# Имена сервисов (без .service).
APP   := pd-tradebot
ADMIN := pd-tradebot-admin

# Куда systemd ищет unit-файлы.
UNIT_DIR := /etc/systemd/system

.PHONY: install start stop logs logs-app logs-admin

# Перенос unit-файлов в systemd и перечитывание конфигов.
install:
	cp $(APP).service $(ADMIN).service $(UNIT_DIR)/
	systemctl daemon-reload

# Запуск сервисов + автозапуск после ребута.
start:
	systemctl enable --now $(APP) $(ADMIN)

# Остановка сервисов + отключение автозапуска.
stop:
	systemctl disable --now $(APP) $(ADMIN)

# Логи обоих сервисов вживую (Ctrl+C для выхода).
logs:
	journalctl -u $(APP) -u $(ADMIN) -f
