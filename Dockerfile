FROM public.ecr.aws/lambda/python:3.11

COPY requirements-lambda.txt .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements-lambda.txt

COPY backend/ backend/
COPY data/ data/

CMD ["backend.lambda_handler.handler"]
