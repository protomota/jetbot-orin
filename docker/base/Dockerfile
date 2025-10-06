ARG BASE_IMAGE=dustynv/l4t-pytorch:r36.4.0
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_INDEX_URL=https://pypi.org/simple
ENV PIP_EXTRA_INDEX_URL=""

# ====================
# INSTALL COMMON TOOLS
# ====================
RUN apt-get update && apt-get install -y net-tools vim cmake

# ==============
# INSTALL OPENCV
# ==============
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
            python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# =================
# INSTALL GSTREAMER
# =================
RUN apt-get update && \
    apt-get install -y \
    libwayland-egl1 \
    gstreamer1.0-plugins-bad \
    libgstreamer-plugins-bad1.0-0 \
    gstreamer1.0-plugins-good \
    python3-gst-1.0 \
    && rm -rf /var/lib/apt/lists/*

# =======================
# INSTALL JUPYTER RELATED
# =======================
RUN apt-get update && \
    apt-get install -y curl nodejs npm libffi-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --index-url https://pypi.org/simple --no-cache-dir \
    traitlets \
    jupyter \
    jupyterlab \
    ipywidgets

RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager || true

# Install jupyter_clickable_image_widget
RUN cd /tmp && \
    git clone https://github.com/jaybdub/jupyter_clickable_image_widget && \
    cd jupyter_clickable_image_widget && \
    pip3 install --index-url https://pypi.org/simple -e . && \
    jupyter labextension install js || true && \
    jupyter lab build || true && \
    cd / && rm -rf /tmp/jupyter_clickable_image_widget
    
# ============================
# INSTALL MISC DEPENDENCIES
# ============================
RUN apt-get update && \
    apt-get install -y supervisor unzip python3-smbus && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --index-url https://pypi.org/simple --no-cache-dir pyzmq

# =================
# INSTALL TORCH2TRT
# =================
# torch2trt is already installed in the dustynv/l4t-pytorch base image

# ==============
# INSTALL JETBOT
# ==============
ENV JETBOT_REPO_DIR=/opt/jetbot
COPY . ${JETBOT_REPO_DIR}
RUN cd ${JETBOT_REPO_DIR} && python3 setup.py install
