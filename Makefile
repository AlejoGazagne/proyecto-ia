.PHONY: help build up down restart logs clean test health docs

# Variables
COMPOSE=docker-compose
PYTHON=python3

help: ## Mostrar ayuda
	@echo "ETH Security Toolbox - Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construir todos los contenedores
	$(COMPOSE) build

up: ## Iniciar todos los servicios
	$(COMPOSE) up -d

down: ## Detener todos los servicios
	$(COMPOSE) down

restart: ## Reiniciar todos los servicios
	$(COMPOSE) restart

logs: ## Ver logs de todos los servicios
	$(COMPOSE) logs -f

logs-api: ## Ver logs del servicio API
	$(COMPOSE) logs -f api

logs-slither: ## Ver logs del servicio Slither
	$(COMPOSE) logs -f slither

logs-solc: ## Ver logs del servicio Solc
	$(COMPOSE) logs -f solc

logs-medusa: ## Ver logs del servicio Medusa
	$(COMPOSE) logs -f medusa

logs-echidna: ## Ver logs del servicio Echidna
	$(COMPOSE) logs -f echidna

clean: ## Limpiar contenedores, volúmenes y datos
	$(COMPOSE) down -v
	docker system prune -f

clean-all: ## Limpiar todo incluyendo imágenes
	$(COMPOSE) down -v --rmi all
	docker system prune -af

test: ## Ejecutar suite de tests
	$(PYTHON) test_system.py

health: ## Verificar estado de los servicios
	curl -s http://localhost:8000/health | $(PYTHON) -m json.tool

status: ## Mostrar estado de los contenedores
	$(COMPOSE) ps

stats: ## Mostrar uso de recursos
	docker stats --no-stream

rebuild: down build up ## Reconstruir y reiniciar todo

rebuild-api: ## Reconstruir solo el servicio API
	$(COMPOSE) build api
	$(COMPOSE) up -d api

rebuild-slither: ## Reconstruir solo el servicio Slither
	$(COMPOSE) build slither
	$(COMPOSE) up -d slither

rebuild-solc: ## Reconstruir solo el servicio Solc
	$(COMPOSE) build solc
	$(COMPOSE) up -d solc

rebuild-medusa: ## Reconstruir solo el servicio Medusa
	$(COMPOSE) build medusa
	$(COMPOSE) up -d medusa

rebuild-echidna: ## Reconstruir solo el servicio Echidna
	$(COMPOSE) build echidna
	$(COMPOSE) up -d echidna

docs: ## Abrir documentación interactiva en el navegador
	@echo "Abriendo documentación en http://localhost:8000/docs"
	xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Abrir manualmente: http://localhost:8000/docs"

shell-api: ## Acceder al shell del contenedor API
	docker exec -it eth-security-api bash

shell-slither: ## Acceder al shell del contenedor Slither
	docker exec -it eth-security-slither bash

shell-solc: ## Acceder al shell del contenedor Solc
	docker exec -it eth-security-solc bash

shell-medusa: ## Acceder al shell del contenedor Medusa
	docker exec -it eth-security-medusa bash

shell-echidna: ## Acceder al shell del contenedor Echidna
	docker exec -it eth-security-echidna bash

workspace: ## Ver contenido del volumen compartido
	docker run --rm -v eth_shared_workspace:/workspace alpine ls -la /workspace

clean-workspace: ## Limpiar archivos del volumen compartido
	docker run --rm -v eth_shared_workspace:/workspace alpine sh -c "rm -rf /workspace/*"

install: build up ## Instalación completa (build + up)
	@echo "✅ Sistema instalado correctamente"
	@echo "🌐 API disponible en: http://localhost:8000"
	@echo "📚 Documentación en: http://localhost:8000/docs"
	@echo "🔧 n8n disponible en: http://localhost:5678"
	@echo ""
	@echo "Ejecuta 'make test' para probar el sistema"

dev: ## Modo desarrollo (logs en tiempo real)
	$(COMPOSE) up --build
