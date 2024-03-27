FROM public.ecr.aws/lambda/python:3.10

COPY ./src/requirements.txt ./
RUN pip install -r requirements.txt

COPY ./src/nationguessr ./nationguessr
COPY ./src/lambda.py ./lambda.py
COPY ./data/data.db ./

CMD [ "lambda.handler" ]
