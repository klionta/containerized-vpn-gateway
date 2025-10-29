# containerized-vpn-gateway
A containerized secure VPN gateway using Python, WireGuard, and Docker.

containerized-vpn-gateway/
├── vpn_gateway/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── wg0.conf.template
│
├── control_server/
│   ├── app.py
│   ├── vpn_manager.py
│   ├── Dockerfile
│
├── client/
│   ├── Dockerfile
│   ├── connect.sh
│
├── database/
│   ├── users.db
│
├── tests/
│
├── docker-compose.yml
├── requirements.txt
├── .github/
│   └── workflows/
│       └── ci.yml
└── README.md
