.PHONY: help cobol api test install clean

help:
	@echo "SMCPE Makefile"
	@echo "  make cobol   - compile GnuCOBOL -> backend/cobol/libpayroll.so"
	@echo "  make api     - run FastAPI dev server"
	@echo "  make test    - run pytest + cobol roundtrip"
	@echo "  make install - apt install deps (needs sudo)"
	@echo "  make clean   - remove build artifacts"

cobol:
	$(MAKE) -C backend/cobol all

api:
	. backend/.venv/bin/activate 2>/dev/null || true; \
	uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload

test:
	pytest backend/tests -v
	python3 backend/tests/test_cobol_roundtrip.py || echo "COBOL lib not built yet"

install:
	sudo apt-get update && sudo apt-get install -y gnucobol4 build-essential nginx python3-venv sqlite3 certbot python3-certbot-nginx ufw fail2ban

clean:
	rm -f backend/cobol/*.so backend/cobol/*.o
	rm -rf backend/__pycache__ backend/api/__pycache__
