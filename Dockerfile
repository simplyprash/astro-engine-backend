FROM public.ecr.aws/lambda/python:3.11

# Install deps without caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy only app code (nothing else)
COPY app ${LAMBDA_TASK_ROOT}/app

CMD ["app.lambda_handler.handler"]
