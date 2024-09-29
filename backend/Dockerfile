FROM python:3.12
# 
WORKDIR /app
# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/
#
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == true ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"
#
ENV PYTHONPATH=/app
#
COPY ./scripts/ /app/scripts
#
COPY ./tests-start.sh /app/
#
COPY ./app /app/app
#
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
