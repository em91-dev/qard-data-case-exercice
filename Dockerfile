
FROM ubuntu:20.04

ENV PATH="/root/miniconda3/bin:${PATH}"
ENV ARG="/root/miniconda3/bin:${PATH}"

EXPOSE 8888


RUN apt update \
    && apt install -y python3-dev wget git \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir root/.conda \
    && sh Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh

ENV TZ=Europe/Paris
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt install -y tesseract-ocr \
    && apt install -y poppler-utils \
    && apt install -y default-jdk

RUN conda create -y -n sparkenv python=3.7 \
    && /bin/bash -c "source activate sparkenv && \
                     pip install pandas pyspark pytesseract pdf2image spacy && \
                     python -m spacy download fr_core_news_md"




