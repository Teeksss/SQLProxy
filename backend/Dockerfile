# Example additions to your backend/Dockerfile

# ... (your existing Python setup, WORKDIR, requirements installation) ...

# If your Python app serves static files from a directory, e.g., /app/static
# And your frontend build output is in frontend/dist/ at the repo root
# Create the target directory in the image
RUN mkdir -p /app/static/frontend 
# Copy the built frontend assets
COPY frontend/dist /app/static/frontend

# Make sure your application code is copied after static assets if paths overlap
# or if you want to ensure backend code is "on top"
COPY . /app 
# Or if your backend code is in a subdirectory from the Dockerfile's perspective when context is '.'
# COPY backend/ /app

# WORKDIR /app # Or /app/backend if your app code is there

# ... (rest of your Dockerfile: EXPOSE, CMD) ...