#!/bin/bash

# TLDR News Aggregator - Start Script
# This script starts both the backend API server and frontend webapp

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_DIR="logs"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup background processes
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend server stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

print_status "Starting TLDR News Aggregator..."

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    print_error "Expected to find 'backend' and 'frontend' directories"
    exit 1
fi

# Start backend server
print_status "Starting backend API server..."
cd backend

# Check if uv is available
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first:"
    print_error "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Start backend in background
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../$LOG_DIR/backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Failed to start backend server. Check backend.log for details."
    cat ../logs/backend.log
    exit 1
fi

print_success "Backend server started on http://localhost:8000"
print_status "API documentation available at http://localhost:8000/docs"

cd ..

# Start frontend server
print_status "Starting frontend webapp..."
cd frontend

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install Node.js and npm first."
    cleanup
    exit 1
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "node_modules not found. Installing dependencies..."
    npm install
fi

# Start frontend in background
npm run dev > ../$LOG_DIR/frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    print_error "Failed to start frontend server. Check frontend.log for details."
    cat ../$LOG_DIR/frontend.log
    cleanup
    exit 1
fi

print_success "Frontend webapp started on http://localhost:5173"

cd ..

print_success "🚀 TLDR News Aggregator is now running!"
echo ""
print_status "Services:"
print_status "  • Backend API: http://localhost:8000"
print_status "  • API Docs: http://localhost:8000/docs"
print_status "  • Frontend: http://localhost:5173"
echo ""
print_status "Logs are being written to backend.log and frontend.log"
print_status "Press Ctrl+C to stop both services"

# Wait for user to interrupt
while true; do
    sleep 1
done 