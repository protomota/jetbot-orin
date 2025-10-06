ARG BASE_IMAGE=jetbot/jetbot:models-0.4.3-36.4.4
FROM ${BASE_IMAGE}

ARG JUPYTER_PASSWORD=jetbot
ENV JUPYTER_WORKDIR=/workspace
WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y ssh && \
    rm -rf /var/lib/apt/lists/*

# ====================
# SET JUPYTER PASSWORD
# ====================
ENV JUPYTER_PASSWORD=${JUPYTER_PASSWORD}
RUN jupyter lab --generate-config -y

# Create a Python script to set the password
RUN cat > /tmp/set_pwd.py << 'EOFPYTHON'
from jupyter_server.auth import passwd
pw = passwd('jetbot')
with open('/root/.jupyter/jupyter_lab_config.py', 'a') as f:
    f.write(f"c.ServerApp.password = '{pw}'\n")
EOFPYTHON

RUN python3 /tmp/set_pwd.py && rm /tmp/set_pwd.py

ENV SHELL=/bin/bash

CMD cd $JUPYTER_WORKDIR && jupyter lab --ip 0.0.0.0 --port 8888 --allow-root
