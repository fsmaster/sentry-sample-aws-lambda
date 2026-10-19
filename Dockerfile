FROM public.ecr.aws/lambda/python:3.13
ARG RELEASE=dev
ENV RELEASE=${RELEASE}
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
ENV AWS_LAMBDA_FUNCTION_TIMEOUT=3
CMD ["lambda_function.lambda_handler"]
