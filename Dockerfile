FROM python:3.7-alpine

COPY . ./mr_gibbs
WORKDIR /mr_gibbs
RUN pip install -r requirements.txt

ENV PYTHONPATH "${PYTHONPATH}:/mr_gibbs/src"

CMD ["python", "run.py"]
