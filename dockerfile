FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    POETRY_VERSION=1.6.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    # WeasyPrint dependencies
    libpango1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libglib2.0-0 \
    libcairo2 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Set working directory
WORKDIR /app

COPY . .

# Copy only dependency files first
#COPY pyproject.toml poetry.lock* README.md ./


# Debug: List files
RUN ls -la

# Install external dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-ansi

# Create the /app/src directory
#RUN mkdir -p /app/src

# Copy the rest of the application
#COPY ./src/ /app/src
# COPY ./src/templates ./templates
# COPY ./src/static ./static
# COPY .env ./.env



# Install project dependencies from pyproject.toml
#RUN poetry install --no-ansi

# Run the application
CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]