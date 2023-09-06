FROM python:3.10.8-bullseye

COPY requirements.txt .
RUN pip3 install -r requirements.txt -vvv

WORKDIR /app
COPY . /app

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]
