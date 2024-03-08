FROM public.ecr.aws/lambda/python:3.10

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY ./src/ ./
COPY ./data/data.db ./

CMD [ "lambda.handler" ]
