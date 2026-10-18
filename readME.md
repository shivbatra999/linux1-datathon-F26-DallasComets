## A GUIDE TO OUR PROJECT ##
Authors: Shivansh Batra, Arman Sarder, Eshwar Singh Rajaputana, MUHD Ayman Haque
Project DESC:

### IBM Granite on LinuxONE

Run `docker compose up -d --build` on LinuxONE (s390x).
Granite 4.2 3B Q4_K_M runs on CPU using llama.cpp with one request slot.
The first startup downloads about 2.24 GB from IBM and converts the weights
to big-endian for LinuxONE, cached in `granite_models`.
The runtime uses Ubuntu 26.04 for the converter's NumPy 2 dependency.

To upgrade an existing installation, copy `compose.yaml` and the entire
`docker/granite` directory to the host, then run:

```sh
docker compose build --no-cache granite
docker compose up -d granite
docker compose logs -f granite
```

The fresh build updates llama.cpp for Granite 4.2 support. Existing Granite
3.3 weights remain in the volume but are no longer loaded.

API: `http://localhost:8080/v1` (or `http://granite:8080/v1` within Compose),
with model name `granite`.
