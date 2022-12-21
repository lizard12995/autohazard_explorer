# Container for building the environment
FROM condaforge/mambaforge:latest as conda

COPY environment.yml .
RUN mamba env create -p /env --file environment.yml && conda clean -afy
COPY . /pkg

WORKDIR /pkg
RUN ls
