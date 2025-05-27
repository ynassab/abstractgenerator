# Adapted from https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

ARG BUILD_DIR="build"
ARG RUNTIME_VERSION="3.10"
ARG TF_WHEEL_NAME="tensorflow-2.9.2-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"

FROM public.ecr.aws/lambda/python:${RUNTIME_VERSION}

ARG BUILD_DIR
ARG TF_WHEEL_NAME

COPY ${BUILD_DIR}/requirements.txt ${LAMBDA_TASK_ROOT}
COPY ${BUILD_DIR}/${TF_WHEEL_NAME} ${LAMBDA_TASK_ROOT}

# Install the function's dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ${TF_WHEEL_NAME}

# Copy the rest of the build code (changes frequently)
COPY /${BUILD_DIR} ${LAMBDA_TASK_ROOT}

# Delete wheel file to reduce size of image
RUN rm ${TF_WHEEL_NAME}

# Pass the name of the function handler as an argument to the runtime
CMD [ "lambda_function.lambda_handler" ]
