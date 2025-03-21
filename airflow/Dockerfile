FROM apache/airflow:2.5.1-python3.8

USER root

# Install gosu
RUN apt-get update && apt-get install -y gosu

USER airflow

# Other configuration (e.g., dependencies) can go here

ENTRYPOINT ["/entrypoint"]
