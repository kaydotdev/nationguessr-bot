FROM public.ecr.aws/lambda/python:3.10

COPY ./src/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src/assets ./assets
COPY ./src/nationguessr ./nationguessr
COPY ./src/lambda.py ./lambda.py

CMD [ "lambda.handler" ]
