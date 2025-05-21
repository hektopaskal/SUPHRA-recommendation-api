FROM mambaorg/micromamba:latest

# Set the working directory
WORKDIR /app

# Copy environment file and install dependencies
COPY environment.yaml /tmp/environment.yaml
RUN micromamba install -y -n base --file /tmp/environment.yaml && \
    micromamba clean --all --yes

#in the docs it is clearly explained that base must be used as docker container environment
# see https://micromamba-docker.readthedocs.io/en/latest/quick_start.html#running-commands-in-dockerfile-within-the-conda-environment


# Add HOST setting to activation script (as root, then return to normal execution)
USER root
RUN echo 'export HOST=0.0.0.0' >> /usr/local/bin/_activate_current_env.sh
USER $MAMBA_USER


# Activate the environment for future commands
SHELL ["micromamba", "run", "-n", "base", "/bin/bash", "-c"]

# Initialize LD_LIBRARY_PATH first to avoid the warning
ENV LD_LIBRARY_PATH=""
# Then set it with the path you need
ENV LD_LIBRARY_PATH="/opt/conda/lib/mariadb:${LD_LIBRARY_PATH}"

# Create symlink for the MariaDB library if needed
RUN ln -sf /opt/conda/lib/mariadb/libmariadb.so.3 /opt/conda/lib/libmariadb.so.3 || echo "Symlink creation failed, checking if file exists"

# Verify the library exists
RUN find /opt -name "libmariadb.so.3" || echo "Library not found in /opt"

# Install MariaDB using pip (again, to catch potential issues)
RUN pip install --no-cache-dir --upgrade mariadb>=1.1.12

# Ensure mariadb_config is available
RUN which mariadb_config || echo "mariadb_config not found"

# Copy the application code
COPY . ./

# Use a different environment variable name to avoid collision with conda's HOST
ENV HOST=0.0.0.0
ENV DASH_HOST=0.0.0.0

# Expose port 8050 for Dash app
EXPOSE 8050


# Update ENTRYPOINT to use APP_HOST instead of HOST
#ENTRYPOINT ["micromamba", "run", "-n", "base", "-e", "HOST=0.0.0.0", "-e", "LD_LIBRARY_PATH=/opt/conda/lib/mariadb:${LD_LIBRARY_PATH:-}"]
CMD ["python", "/app/app.py"]
