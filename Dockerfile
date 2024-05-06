# syntax=docker/dockerfile:experimental

FROM isas/isas_base:python3.11.8-poetry1.7.1

COPY pyproject.toml poetry.toml poetry.lock $WORKDIR/
RUN pip install --upgrade pip
RUN --mount=type=ssh \
 mkdir -p -m 0600 ~/.ssh \
 && ssh-keyscan -H github.com >> ~/.ssh/known_hosts \
 && poetry install --no-root

RUN echo "alias flake8='pflake8'" >> $HOME/.bashrc

CMD ["bash"]
