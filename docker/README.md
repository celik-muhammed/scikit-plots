# 🚀 Docker

### 💡 Work on `Docker Desktop` or `Github Codespaces`

## Docker Environment Setup for Jupyter and/or NVIDIA GPU

- This repository contains Docker & Docker Compose configurations for running Jupyter Notebooks with optional NVIDIA GPU support.
- You can run containers with either host-installed CUDA or pre-installed CUDA inside the container.

## 📂 Folder Structure

📁 docker/  
 ├── 📄 docker-compose.yml           # Primary Docker Compose file  
 ├── 📄 docker-compose.override.yml  # Optional override file (auto-included if present)  
 ├── 📄 Dockerfile                   # Custom Dockerfile  
 ├── 🗜️ script/  
 │   ├── 📝 install_gpu_nvidia_cuda.sh  # GPU setup script  

## 🏷️ Quick Start (Docker Compose)

### 💡 The easiest way to launch the environment is using Docker Compose.

▶️ Run Jupyter Notebook (CPU only)

```sh
docker compose up --build notebook_cpu
```

▶️ Run Jupyter Notebook (With NVIDIA Host GPU)

```sh
docker compose up --build app_nvidia_host_gpu_driver
```

▶️ Run Jupyter Notebook (With NVIDIA Internal CUDA GPU)

```sh
docker compose up --build app_nvidia_internal_gpu_driver
```

🚯 Stop Containers

```sh
docker compose down
```

## 🐳 Docker Compose Configuration

This project is based on Docker Compose and includes multiple services:

🔹 `notebook_cpu` (CPU-Only)

Runs Jupyter Notebook using `jupyter/tensorflow-notebook:latest`

No CUDA support, best for lightweight tasks

Mounts the local folder `scikit-plots` to `/home/jovyan/work`

Runs on ports `8888`

🔹 `app_nvidia_host_gpu_driver` (Uses Host CUDA)

Runs Jupyter Notebook using `jupyter/tensorflow-notebook:latest`

Uses `host-installed CUDA` for GPU acceleration

Requires NVIDIA runtime enabled (--runtime=nvidia)

Runs on port `8888`

🔹 `app_nvidia_internal_gpu_driver` (CUDA Inside Container)

Runs `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04` with pre-installed CUDA

Includes NVIDIA GPU support `without needing host CUDA`

Requires NVIDIA runtime (--runtime=nvidia)

Runs on port `8889`

## 🛠️ Custom Docker Commands

If you need more control, you can use Docker CLI commands.

▶️ Build & Run the Container Manually

```sh
docker build -t my-custom-container -f docker/Dockerfile .
docker run -it --rm -p 8888:8888 my-custom-container
```

▶️ Check GPU Availability Inside Container

```sh
docker exec -it <container_id> nvidia-smi
```

## 🖥️ Useful References

📚 [Jupyter Docker Stacks: Read the Docs](https://jupyter-docker-stacks.readthedocs.io/en/latest/)

📚 [Docker Compose: Official Docs](https://docs.docker.com/compose/)

📚 [NVIDIA CUDA in Containers: NVIDIA Docs](https://docs.nvidia.com/deeplearning/frameworks/user-guide/index.html)

- https://containers.dev/guide/dockerfile

- https://docs.localstack.cloud/getting-started/installation/#docker-compose

<div align=center><br>

[![](https://developer-blogs.nvidia.com/wp-content/uploads/2016/06/nvidia-docker.png)](https://developer.nvidia.com/blog/nvidia-docker-gpu-server-application-deployment-made-easy/)

</div>

🚀 Now you're ready to run Jupyter notebooks in Docker! 😊
