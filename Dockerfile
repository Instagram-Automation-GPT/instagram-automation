# Use an official Python runtime as a parent image
FROM python:3.9-slim

WORKDIR /home/instagramautomation

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment in the container
RUN python3 -m venv /venv

# Use the virtual environment's pip to install dependencies
COPY requirements.txt .
RUN /venv/bin/pip install --upgrade pip && /venv/bin/pip install --no-cache-dir -r requirements.txt
RUN /venv/bin/pip install moviepy==1.0.3 --no-cache-dir
# Add venv to PATH
ENV PATH="/venv/bin:$PATH"

# Copy the app code
COPY . .

# Create a script to migrate DB, create superuser, and run server
RUN echo '#!/bin/bash\n\
python manage.py migrate\n\
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser(\"admin\", \"admin@example.com\", \"admin123\") if not User.objects.filter(username=\"admin\").exists() else None" | python manage.py shell\n\
python manage.py runserver 0.0.0.0:8000' > start.sh && chmod +x start.sh

EXPOSE 8000
EXPOSE 8025

CMD ["./start.sh"]
