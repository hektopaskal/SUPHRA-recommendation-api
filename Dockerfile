FROM mambaorg/micromamba:latest

# Set working directory
WORKDIR /app

# Copy and install environment
COPY environment.yaml /tmp/environment.yaml
RUN micromamba install -y -n base --file /tmp/environment.yaml && \
    micromamba clean --all --yes

# Add HOST setting to activation script
USER root
RUN echo 'export HOST=0.0.0.0' >> /usr/local/bin/_activate_current_env.sh
USER $MAMBA_USER

# Activate environment for following commands
SHELL ["micromamba", "run", "-n", "base", "/bin/bash", "-c"]

# Copy your application code
COPY . ./

# Set environment variables
ENV HOST=0.0.0.0
ENV DASH_HOST=0.0.0.0

# Expose the application port
EXPOSE 8050

# Run the application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8050"]
