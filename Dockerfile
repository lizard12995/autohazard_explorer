# Container for building the environment
FROM condaforge/mambaforge:latest as conda

COPY environment.yml .
RUN mamba env create -p /env --file environment.yml && conda clean -afy
COPY . /pkg

WORKDIR /pkg
RUN ls

CMD /env/bin/panel serve --address="0.0.0.0" --port=$PORT app.ipynb --allow-websocket-origin=autohazard-explorer.onrender.com
