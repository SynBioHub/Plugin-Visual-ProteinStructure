FROM python:3.9.7

RUN apt update
RUN apt install -y pymol

COPY . .
RUN pip3 install -r requirements.txt

EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["waitress-serve", "--port=5000", "app:app" ]
