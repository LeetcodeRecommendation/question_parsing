FROM python:3.12-slim-bookworm
COPY . /usr/src/app
WORKDIR /usr/src/app
RUN chmod -R 777 ./
RUN python3 -m ensurepip --upgrade
RUN pip3 install -r ./requirements.txt
RUN python3 setup.py install
ENTRYPOINT ["python3", "./question_parsing/main.py"]