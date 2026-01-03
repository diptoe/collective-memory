#!/usr/bin/env python3
"""
Collective Memory Platform - Application Entry Point

Run with: python run.py
"""
from api import create_app
from api import config

app = create_app()

if __name__ == '__main__':
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║           Collective Memory Platform                       ║
    ║           by Diptoe                                        ║
    ╠════════════════════════════════════════════════════════════╣
    ║  API:      http://{config.API_HOST}:{config.API_PORT}/api             ║
    ║  Swagger:  http://{config.API_HOST}:{config.API_PORT}/api/docs        ║
    ║  Env:      {config.ENV_TYPE.ljust(44)}  ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.DEBUG
    )
