.PHONY: runserver frontend backend \
	desktop-installers desktop-build desktop-frontend desktop-backend \
	desktop-copy-sidecar desktop-tauri-build desktop-clean

FRONTEND_DIR=./frontend
BACKEND_DIR=./backend
TAURI_DIR=./src-tauri
TAURI_BIN_DIR=$(TAURI_DIR)/bin
BACKEND_DIST=$(BACKEND_DIR)/dist
SIDECAR_NAME=melodii-backend
TAURI_TARGET=x86_64-pc-windows-msvc
SIDECAR_TARGET_NAME=$(SIDECAR_NAME)-$(TAURI_TARGET).exe

runserver: frontend backend

frontend:
	$(MAKE) -C $(FRONTEND_DIR) runserver

backend:
	$(MAKE) -C $(BACKEND_DIR) runserver


# Desktop build pipeline
installers: desktop-build
	@echo "Installers are in $(TAURI_DIR)/target/release/bundle/"

desktop-build: desktop-frontend desktop-backend desktop-copy-sidecar desktop-tauri-build

desktop-frontend:
	cd $(FRONTEND_DIR) && npm install
	cd $(FRONTEND_DIR) && npm run build

desktop-backend:
	cd $(BACKEND_DIR) && uv sync
	cd $(BACKEND_DIR) && uv run pyinstaller melodii_backend.spec

tauri: desktop-copy-sidecar desktop-tauri-build

desktop-copy-sidecar:
# 	mkdir -p $(TAURI_BIN_DIR)
# 	@if [ -f $(BACKEND_DIST)/$(SIDECAR_NAME).exe ]; then \
# 		cp $(BACKEND_DIST)/$(SIDECAR_NAME).exe $(TAURI_BIN_DIR)/; \
# 	else \
# 		cp $(BACKEND_DIST)/$(SIDECAR_NAME) $(TAURI_BIN_DIR)/; \
# 	fi
	powershell -Command "New-Item -ItemType Directory -Force -Path $(TAURI_BIN_DIR)"
	powershell -Command "if (Test-Path '$(BACKEND_DIST)/$(SIDECAR_NAME).exe') { Copy-Item '$(BACKEND_DIST)/$(SIDECAR_NAME).exe' '$(TAURI_BIN_DIR)/$(SIDECAR_TARGET_NAME)' -Force } else { Copy-Item '$(BACKEND_DIST)/$(SIDECAR_NAME)' '$(TAURI_BIN_DIR)/$(SIDECAR_TARGET_NAME)' -Force }"


desktop-tauri-build:
	cd $(TAURI_DIR) && cargo tauri build


# cargo install tauri-cli --version ^2


desktop-clean:
	rm -rf $(TAURI_BIN_DIR)

diff-staged:
	git diff --cached > ./a.diff
	code ./a.diff
	rm ./a.diff

diff+: diff-staged


diff-unstaged:
	git diff > ./a.diff
	code ./a.diff
	rm ./a.diff

diff: diff-unstaged


wiff:
	dit diff > ./a.diff
	windsurf ./a.diff
	rm ./a.diff


wiff+:
	git diff --cached > ./a.diff
	windsurf ./a.diff
	rm ./a.diff

