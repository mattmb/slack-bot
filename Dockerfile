FROM python:2
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD ["python", "-u", "bot.py"]
